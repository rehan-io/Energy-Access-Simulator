
from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite


ACCESS_INDICATORS = (
    "elec_access_total",
    "elec_access_rural",
    "elec_access_urban",
    "clean_cooking_access",
)

DEFAULT_TREND_WINDOW = 10  #No of years used for prediction


def estimate_annual_trend(
    observations: Sequence[Mapping[str, float]],
    window: int = DEFAULT_TREND_WINDOW,
) -> dict:
    """Estimate a least-squares annual trend from recent valid observations.

    Each observation must contain:
        year: calendar year
        value: percentage in [0, 100]"""

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

    # If an indicator has multiple observations in one year, fail rather than silently choosing one.
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


def run_access_simulation(
    historical_data: Mapping[str, Sequence[Mapping[str, float]]],
    years: int = 25,
    trend_window: int = DEFAULT_TREND_WINDOW,
    policy_adjustments: Mapping[str, float] | None = None,
) -> dict:
    """Project evidence-backed access indicators.

    `policy_adjustments` maps indicator names to hypothetical annual
    percentage-point adjustments.
    """

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

    trends = {}

    for indicator in ACCESS_INDICATORS:
        observations = historical_data.get(indicator, [])

        if not observations:
            raise ValueError(f"Missing historical data for {indicator}")

        trends[indicator] = estimate_annual_trend(
            observations,
            window=trend_window,
        )

    # Start after the latest observation across all required indicators.
    # This avoids presenting a forecast as an observed historical value.
    baseline_year = max(
        result["latest_year"] for result in trends.values()
    )

    history = []

    # Merge historical observations by year. Missing observations remain
    # None; they are never filled with zero or interpolated silently.
    historical_by_year = {}

    for indicator in ACCESS_INDICATORS:
        for item in historical_data[indicator]:
            year = int(item["year"])
            value = item.get("value")

            if value is not None:
                value = float(value)

            historical_by_year.setdefault(year, {})[indicator] = value

    for year in sorted(historical_by_year):
     if year > baseline_year:
        continue

     row = {
        "year": year,
        "kind": "historical",
        }

     row.update(historical_by_year[year])
     history.append(row)
    for indicator in ACCESS_INDICATORS:
            row[indicator] = historical_by_year[year].get(indicator)
            history.append(row)

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
