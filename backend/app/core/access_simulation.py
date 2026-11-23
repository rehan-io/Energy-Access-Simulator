from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any

from app.core.simulation import run_coupled_simulation
from app.model.calibration_schema import SimulationMacroContext


ACCESS_INDICATORS = (
    "elec_access_total",
    "elec_access_rural",
    "elec_access_urban",
    "clean_cooking_access",
)

POLICY_LEVER_KEYS = (
    "subsidy",
    "carbon_tax",
    "off_grid",
    "grid_ext",
)

DEFAULT_TREND_WINDOW = 10  # No of years used for prediction


def estimate_annual_trend(
    observations: Sequence[Mapping[str, float]],
    window: int = DEFAULT_TREND_WINDOW,
) -> dict:
    """Estimate a least-squares annual trend from recent valid observations.

    Each observation must contain:
        year: calendar year
        value: percentage in [0, 100]
    """

    if window < 2:
        raise ValueError("window must be at least 2")

    valid = []

    for item in observations:
        year = item.get("year")
        value = item.get("value")

        if year is None or value is None:
            continue

        year = int(year)
        value = float(value)

        if not 0 <= value <= 100 or not isfinite(value):
            raise ValueError("Access observations must be finite percentages")

        valid.append((year, value))

    years = [year for year, _ in valid]
    if len(years) != len(set(years)):
        raise ValueError("Duplicate observation years are not allowed")

    valid.sort(key=lambda pair: pair[0])
    selected = valid[-window:]

    if len(selected) < 2:
        raise ValueError(
            f"At least two valid observations are required; got {len(selected)}"
        )

    x = [float(year) for year, _ in selected]
    y = [value for _, value in selected]

    x_mean = sum(x) / len(x)
    y_mean = sum(y) / len(y)

    denominator = sum((value - x_mean) ** 2 for value in x)

    if denominator == 0:
        raise ValueError("Observation years must not all be identical")

    slope = sum(
        (x_value - x_mean) * (y_value - y_mean)
        for x_value, y_value in zip(x, y)
    ) / denominator

    return {
        "latest_year": selected[-1][0],
        "latest_value": selected[-1][1],
        "annual_trend": slope,
        "observations_used": len(selected),
        "window": window,
        "first_year_used": selected[0][0],
        "last_year_used": selected[-1][0],
    }


def _normalize_historical_data(
    historical_data: Mapping[str, Sequence[Mapping[str, float]]],
    trend_window: int,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict], int, list[dict[str, Any]]]:
    normalized_data: dict[str, list[dict[str, Any]]] = {}

    for indicator in ACCESS_INDICATORS:
        observations = historical_data.get(indicator, [])

        if not observations:
            raise ValueError(f"Missing historical data for {indicator}")

        merged: dict[int, float | None] = {}

        for item in observations:
            year = int(item["year"])
            value = item.get("value")

            if value is not None:
                value = float(value)

            if year not in merged:
                merged[year] = value
                continue

            existing_value = merged[year]

            if existing_value is None and value is not None:
                merged[year] = value
            elif (
                existing_value is not None
                and value is not None
                and existing_value != value
            ):
                raise ValueError(
                    f"Conflicting duplicate observations for "
                    f"{indicator} in {year}: "
                    f"{existing_value} and {value}"
                )

        normalized_data[indicator] = [
            {"year": year, "value": value}
            for year, value in sorted(merged.items())
        ]

    trends = {
        indicator: estimate_annual_trend(
            normalized_data[indicator],
            window=trend_window,
        )
        for indicator in ACCESS_INDICATORS
    }

    baseline_year = max(result["latest_year"] for result in trends.values())

    historical_by_year: dict[int, dict[str, float | None]] = {}
    for indicator in ACCESS_INDICATORS:
        for item in normalized_data[indicator]:
            year = item["year"]
            historical_by_year.setdefault(year, {})[indicator] = item["value"]

    history: list[dict[str, Any]] = []
    for year in sorted(historical_by_year):
        if year > baseline_year:
            continue

        row: dict[str, Any] = {
            "year": year,
            "kind": "historical",
        }
        for indicator in ACCESS_INDICATORS:
            row[indicator] = historical_by_year[year].get(indicator)
        history.append(row)

    return normalized_data, trends, baseline_year, history


def run_access_simulation(
    historical_data: Mapping[str, Sequence[Mapping[str, float]]],
    years: int = 25,
    trend_window: int = DEFAULT_TREND_WINDOW,
    policy_adjustments: Mapping[str, float] | None = None,
) -> dict:
    """Project evidence-backed access indicators (legacy linear adjustment mode)."""

    if years < 1 or years > 100:
        raise ValueError("years must be between 1 and 100")

    policy_adjustments = policy_adjustments or {}

    unknown = set(policy_adjustments) - set(ACCESS_INDICATORS)
    if unknown:
        raise ValueError(f"Unknown policy adjustment indicators: {sorted(unknown)}")

    for indicator, adjustment in policy_adjustments.items():
        if not isfinite(float(adjustment)):
            raise ValueError(
                f"Policy adjustment for {indicator} must be finite"
            )

    _, trends, baseline_year, history = _normalize_historical_data(
        historical_data,
        trend_window,
    )

    current = {
        indicator: trends[indicator]["latest_value"]
        for indicator in ACCESS_INDICATORS
    }

    for step in range(1, years + 1):
        projected_year = baseline_year + step
        row = {
            "year": projected_year,
            "kind": "projected",
        }

        for indicator in ACCESS_INDICATORS:
            trend = trends[indicator]["annual_trend"]
            policy_effect = float(policy_adjustments.get(indicator, 0.0))

            next_value = current[indicator] + trend + policy_effect
            next_value = min(100.0, max(0.0, next_value))

            current[indicator] = next_value
            row[indicator] = round(next_value, 4)

        history.append(row)

    return {
        "baselineYear": baseline_year,
        "trendWindow": trend_window,
        "trends": trends,
        "policyAdjustments": dict(policy_adjustments),
        "history": history,
    }


def run_coupled_access_simulation(
    historical_data: Mapping[str, Sequence[Mapping[str, float]]],
    country_code: str,
    macro: SimulationMacroContext,
    years: int = 25,
    trend_window: int = DEFAULT_TREND_WINDOW,
    policy_levers: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project access indicators & five-tier stocks via the coupled difference model."""

    if years < 1 or years > 100:
        raise ValueError("years must be between 1 and 100")

    levers = dict(policy_levers or {})
    subsidy = float(levers.get("subsidy", 0.0))
    carbon_tax = float(levers.get("carbon_tax", 0.0))
    off_grid = float(levers.get("off_grid", 0.0))
    grid_ext = float(levers.get("grid_ext", 0.0))
    recycle_tax_revenue = bool(levers.get("recycle_tax_revenue", True))

    _, trends, baseline_year, history = _normalize_historical_data(
        historical_data,
        trend_window,
    )

    coupled = run_coupled_simulation(
        country=country_code,
        baseline_year=baseline_year,
        years=years,
        elec_total_pct=trends["elec_access_total"]["latest_value"],
        elec_rural_pct=trends["elec_access_rural"]["latest_value"],
        elec_urban_pct=trends["elec_access_urban"]["latest_value"],
        clean_cooking_pct=trends["clean_cooking_access"]["latest_value"],
        macro=macro,
        subsidy=subsidy,
        carbon_tax=carbon_tax,
        off_grid=off_grid,
        grid_ext=grid_ext,
        recycle_tax_revenue=recycle_tax_revenue,
    )

    # Attach calibrated baseline tier splits to the baseline historical snapshot
    # while leaving earlier historical years null for tier shares.
    for row in history:
        if row["year"] == baseline_year:
            row.update(coupled["baselineStocks"])
        else:
            row.update({
                "traditional": None,
                "lantern": None,
                "shs": None,
                "minigrid": None,
                "grid": None,
            })

    history.extend(coupled["projected"])

    return {
        "baselineYear": baseline_year,
        "trendWindow": trend_window,
        "trends": trends,
        "policyAdjustments": {},
        "policyLevers": {
            "subsidy": subsidy,
            "carbon_tax": carbon_tax,
            "off_grid": off_grid,
            "grid_ext": grid_ext,
            "recycle_tax_revenue": recycle_tax_revenue,
        },
        "modelMode": "coupled",
        "history": history,
    }