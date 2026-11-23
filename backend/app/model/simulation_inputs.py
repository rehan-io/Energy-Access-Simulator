"""Build country-specific historical inputs for simulations."""

from __future__ import annotations

from math import isfinite
from typing import Any

import pandas as pd

from app.core.access_simulation import (
    ACCESS_INDICATORS,
    run_access_simulation,
    run_coupled_access_simulation,
)
from app.data.dataset_loader import load_long_dataset
from app.model.calibration import get_simulation_macro_context


REQUIRED_COLUMNS = {"iso3", "indicator", "year", "value"}


def load_country_historical_data(
    country_code: str,
    data_dir: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Load observed access indicators for one country.

    Missing observations are preserved as None. No interpolation,
    forward-filling, or substitution with another country's data occurs.
    """

    country_code = country_code.strip().upper()

    if not country_code:
        raise ValueError("country_code must not be empty")

    dataset = load_long_dataset(data_dir)

    missing_columns = REQUIRED_COLUMNS - set(dataset.columns)
    if missing_columns:
        raise ValueError(
            f"Processed dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    country_data = dataset.loc[
        dataset["iso3"].astype(str).str.upper() == country_code
    ].copy()

    if country_data.empty:
        raise ValueError(
            f"No processed World Bank observations found for "
            f"country '{country_code}'"
        )

    historical_data: dict[str, list[dict[str, Any]]] = {}

    for indicator in ACCESS_INDICATORS:
        indicator_data = country_data.loc[
            country_data["indicator"] == indicator,
            ["year", "value"],
        ].copy()

        if indicator_data.empty:
            raise ValueError(
                f"No observations found for indicator '{indicator}' "
                f"in country '{country_code}'"
            )

        indicator_data = indicator_data.sort_values("year")

        observations: list[dict[str, Any]] = []

        for row in indicator_data.itertuples(index=False):
            year = int(row.year)

            if pd.isna(row.value):
                value = None
            else:
                value = float(row.value)

                if not isfinite(value):
                    raise ValueError(
                        f"Non-finite value for {country_code}, "
                        f"{indicator}, year {year}"
                    )

            observations.append({
                "year": year,
                "value": value,
            })

        historical_data[indicator] = observations

    return historical_data


def run_country_access_simulation(
    country_code: str,
    years: int = 25,
    trend_window: int = 10,
    policy_adjustments: dict[str, float] | None = None,
    data_dir: str | None = None,
) -> dict[str, Any]:
    """Run the evidence-first simulation using one country's observations."""

    historical_data = load_country_historical_data(
        country_code=country_code,
        data_dir=data_dir,
    )

    result = run_access_simulation(
        historical_data=historical_data,
        years=years,
        trend_window=trend_window,
        policy_adjustments=policy_adjustments,
    )

    result["countryCode"] = country_code.strip().upper()

    return result


def run_country_coupled_simulation(
    country_code: str,
    years: int = 25,
    trend_window: int = 10,
    policy_levers: dict[str, Any] | None = None,
    data_dir: str | None = None,
) -> dict[str, Any]:
    """Run the coupled Bass-Logistic & five-tier stock-and-flow simulation."""

    iso3 = country_code.strip().upper()
    historical_data = load_country_historical_data(
        country_code=iso3,
        data_dir=data_dir,
    )

    latest_years = [
        max(
            int(obs["year"])
            for obs in obs_list
            if obs["value"] is not None
        )
        for obs_list in historical_data.values()
    ]
    baseline_year = max(latest_years)

    macro = get_simulation_macro_context(
        country_code=iso3,
        baseline_year=baseline_year,
        data_dir=data_dir,
    )

    result = run_coupled_access_simulation(
        historical_data=historical_data,
        country_code=iso3,
        macro=macro,
        years=years,
        trend_window=trend_window,
        policy_levers=policy_levers,
    )

    result["countryCode"] = iso3
    return result