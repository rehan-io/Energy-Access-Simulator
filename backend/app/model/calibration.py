"""Build country-level simulation baselines from World Bank data."""

from __future__ import annotations

import pandas as pd

from app.data.dataset_loader import load_long_dataset, load_wide_dataset
from app.model.calibration_schema import (
    CalibratedCountryBaseline,
    CountryBaselineInputs,
    SimulationMacroContext,
)


INDICATOR_FIELDS = {
    "population": "population_total",
    "rural_pop_share": "population_rural_pct",
    "elec_access_total": "electricity_access_total_pct",
    "elec_access_rural": "electricity_access_rural_pct",
    "elec_access_urban": "electricity_access_urban_pct",
    "clean_cooking_access": "clean_cooking_access_pct",
    "elec_use_kwh_pc": "elec_use_kwh_pc",
    "gdp_per_capita_usd": "gdp_per_capita_usd",
    "income_share_q1": "income_share_q1",
    "income_share_q2": "income_share_q2",
    "income_share_q3": "income_share_q3",
    "income_share_q4": "income_share_q4",
    "income_share_q5": "income_share_q5",
}

COUNTRY_NAMES = {
    "IND": "India",
    "KEN": "Kenya",
    "RWA": "Rwanda",
    "NGA": "Nigeria",
}

DEFAULT_MACRO_FALLBACKS = {
    "IND": {
        "rural_pop_share": 0.6462,
        "rural_pop_drift": -0.0031,
        "gdp_per_capita_usd": 2592.0,
        "gdp_growth_rate": 0.045,
        "bottom_80_income_share": 65.8,
        "elec_use_kwh_pc": 1222.8,
    },
    "KEN": {
        "rural_pop_share": 0.6811,
        "rural_pop_drift": -0.0005,
        "gdp_per_capita_usd": 2133.5,
        "gdp_growth_rate": 0.035,
        "bottom_80_income_share": 53.8,
        "elec_use_kwh_pc": 195.3,
    },
    "RWA": {
        "rural_pop_share": 0.7012,
        "rural_pop_drift": -0.0127,
        "gdp_per_capita_usd": 1059.9,
        "gdp_growth_rate": 0.040,
        "bottom_80_income_share": 52.5,
        "elec_use_kwh_pc": 79.3,
    },
    "NGA": {
        "rural_pop_share": 0.3702,
        "rural_pop_drift": -0.0080,
        "gdp_per_capita_usd": 1084.2,
        "gdp_growth_rate": 0.025,
        "bottom_80_income_share": 58.5,
        "elec_use_kwh_pc": 140.6,
    },
}


def get_country_inputs(country_code: str, data_dir=None):
    """Select the latest non-missing observation for each indicator."""

    country_code = country_code.upper()

    if country_code not in COUNTRY_NAMES:
        raise ValueError(f"Unsupported country: {country_code}")

    df = load_long_dataset(data_dir)

    country_data = df[df["iso3"] == country_code].copy()

    if country_data.empty:
        raise ValueError(f"No World Bank data found for {country_code}")

    values = {}
    years = {}

    for indicator, field_name in INDICATOR_FIELDS.items():
        observations = country_data[
            (country_data["indicator"] == indicator)
            & country_data["value"].notna()
        ].sort_values("year")

        if observations.empty:
            values[field_name] = None
            continue

        latest = observations.iloc[-1]

        values[field_name] = float(latest["value"])
        years[indicator] = int(latest["year"])

    population_year = years.get("population")

    if population_year is None:
        raise ValueError(f"Population data unavailable for {country_code}")

    return CountryBaselineInputs(
        iso3=country_code,
        year=population_year,
        observation_years=years,
        **values,
    )


def calibrate_country_baseline(inputs: CountryBaselineInputs):
    """Convert observed rates into population counts."""

    warnings = []
    missing = []

    for indicator in INDICATOR_FIELDS:
        if indicator not in inputs.observation_years:
            missing.append(indicator)

    population = inputs.population_total

    rural_share = inputs.population_rural_pct

    if rural_share is None:
        rural_share = 50.0
        warnings.append(
            "Rural population share unavailable; assumed 50%."
        )

    rural_population = population * rural_share / 100
    urban_population = population - rural_population

    access_rate = inputs.electricity_access_total_pct

    if access_rate is None:
        raise ValueError(
            f"Total electricity access unavailable for {inputs.iso3}"
        )

    access_fraction = access_rate / 100

    electrified = population * access_fraction
    unelectrified = population - electrified

    rural_electrified = None
    urban_electrified = None
    rural_unelectrified = None
    urban_unelectrified = None

    if inputs.electricity_access_rural_pct is not None:
        rural_electrified = (
            rural_population
            * inputs.electricity_access_rural_pct / 100
        )
        rural_unelectrified = rural_population - rural_electrified

    if inputs.electricity_access_urban_pct is not None:
        urban_electrified = (
            urban_population
            * inputs.electricity_access_urban_pct / 100
        )
        urban_unelectrified = urban_population - urban_electrified

    # Check whether independently reported total and rural/urban
    # access rates agree within a tolerance of 2 percentage points.
    if (
        rural_electrified is not None
        and urban_electrified is not None
    ):
        weighted_rate = (
            rural_electrified + urban_electrified
        ) / population * 100

        discrepancy = abs(weighted_rate - access_rate)

        if discrepancy > 2.0:
            warnings.append(
                "Population-weighted rural/urban access differs "
                f"from reported total access by {discrepancy:.2f} "
                "percentage points."
            )

    quintiles = (
        inputs.income_share_q1,
        inputs.income_share_q2,
        inputs.income_share_q3,
        inputs.income_share_q4,
    )
    bottom_80 = (
        float(sum(quintiles))
        if all(q is not None for q in quintiles)
        else None
    )

    return CalibratedCountryBaseline(
        iso3=inputs.iso3,
        year=inputs.year,
        population_total=population,
        population_rural=rural_population,
        population_urban=urban_population,
        population_with_electricity=electrified,
        population_without_electricity=unelectrified,
        electricity_access_rate=access_fraction,
        population_rural_with_electricity=rural_electrified,
        population_urban_with_electricity=urban_electrified,
        population_rural_without_electricity=rural_unelectrified,
        population_urban_without_electricity=urban_unelectrified,
        electricity_access_rural_pct=inputs.electricity_access_rural_pct,
        electricity_access_urban_pct=inputs.electricity_access_urban_pct,
        clean_cooking_access_pct=inputs.clean_cooking_access_pct,
        elec_use_kwh_pc=inputs.elec_use_kwh_pc,
        gdp_per_capita_usd=inputs.gdp_per_capita_usd,
        bottom_80_income_share_pct=bottom_80,
        observation_years=inputs.observation_years,
        missing_indicators=tuple(missing),
        calibration_warnings=tuple(warnings),
    )


def get_calibrated_baseline(country_code: str, data_dir=None):
    """Convenience function for loading and calibrating a country."""

    inputs = get_country_inputs(country_code, data_dir)
    return calibrate_country_baseline(inputs)


def _ols_slope(years: list[int], values: list[float]) -> float:
    n = len(years)
    if n < 2:
        return 0.0
    x_mean = sum(years) / n
    y_mean = sum(values) / n
    denom = sum((y - x_mean) ** 2 for y in years)
    if denom == 0:
        return 0.0
    return sum((x - x_mean) * (v - y_mean) for x, v in zip(years, values)) / denom


def get_simulation_macro_context(
    country_code: str,
    baseline_year: int | None = None,
    data_dir=None,
) -> SimulationMacroContext:
    """Load rural share, urbanization drift, GDP/capita, and B80 from worldbank_wide.csv."""

    iso3 = country_code.strip().upper()
    fallback = DEFAULT_MACRO_FALLBACKS.get(
        iso3,
        {
            "rural_pop_share": 0.55,
            "rural_pop_drift": -0.005,
            "gdp_per_capita_usd": 1500.0,
            "gdp_growth_rate": 0.03,
            "bottom_80_income_share": 60.0,
            "elec_use_kwh_pc": None,
        },
    )

    try:
        wide = load_wide_dataset(data_dir)
    except (FileNotFoundError, ValueError, RuntimeError):
        return SimulationMacroContext(
            iso3=iso3,
            baseline_year=baseline_year or 2024,
            rural_pop_share=fallback["rural_pop_share"],
            rural_pop_drift=fallback["rural_pop_drift"],
            gdp_per_capita_usd=fallback["gdp_per_capita_usd"],
            gdp_growth_rate=fallback["gdp_growth_rate"],
            bottom_80_income_share=fallback["bottom_80_income_share"],
            elec_use_kwh_pc=fallback["elec_use_kwh_pc"],
        )

    country_df = wide[
        wide["iso3"].astype(str).str.upper() == iso3
    ].sort_values("year")

    if country_df.empty:
        return SimulationMacroContext(
            iso3=iso3,
            baseline_year=baseline_year or 2024,
            rural_pop_share=fallback["rural_pop_share"],
            rural_pop_drift=fallback["rural_pop_drift"],
            gdp_per_capita_usd=fallback["gdp_per_capita_usd"],
            gdp_growth_rate=fallback["gdp_growth_rate"],
            bottom_80_income_share=fallback["bottom_80_income_share"],
            elec_use_kwh_pc=fallback["elec_use_kwh_pc"],
        )

    if baseline_year is None:
        access_cols = [
            "elec_access_total",
            "elec_access_rural",
            "elec_access_urban",
            "clean_cooking_access",
        ]
        available_cols = [c for c in access_cols if c in country_df.columns]
        if available_cols:
            valid_access = country_df.dropna(subset=available_cols)
            baseline_year = (
                int(valid_access["year"].max())
                if not valid_access.empty
                else int(country_df["year"].max())
            )
        else:
            baseline_year = int(country_df["year"].max())

    # Rural population share at baseline_year and trailing 10-year urbanization drift.
    rural_share = fallback["rural_pop_share"]
    rural_drift = fallback["rural_pop_drift"]
    if "rural_pop_share" in country_df.columns:
        rur_df = country_df[
            country_df["rural_pop_share"].notna()
            & (country_df["year"] <= baseline_year)
        ]
        if not rur_df.empty:
            rural_share = min(
                0.95,
                max(0.05, float(rur_df.iloc[-1]["rural_pop_share"]) / 100.0),
            )
            recent_rur = rur_df.tail(10)
            if len(recent_rur) >= 2:
                rural_drift = _ols_slope(
                    [int(y) for y in recent_rur["year"]],
                    [float(v) / 100.0 for v in recent_rur["rural_pop_share"]],
                )

    # GDP per capita at baseline_year and clamped trailing 10-year CAGR.
    gdp_pc = fallback["gdp_per_capita_usd"]
    gdp_growth = fallback["gdp_growth_rate"]
    if "gdp_per_capita_usd" in country_df.columns:
        gdp_df = country_df[
            country_df["gdp_per_capita_usd"].notna()
            & (country_df["year"] <= baseline_year)
        ]
        if not gdp_df.empty:
            gdp_pc = float(gdp_df.iloc[-1]["gdp_per_capita_usd"])
            recent_gdp = gdp_df.tail(10)
            if len(recent_gdp) >= 2:
                span = int(recent_gdp.iloc[-1]["year"]) - int(recent_gdp.iloc[0]["year"])
                start_gdp = float(recent_gdp.iloc[0]["gdp_per_capita_usd"])
                end_gdp = float(recent_gdp.iloc[-1]["gdp_per_capita_usd"])
                if span > 0 and start_gdp > 0 and end_gdp > 0:
                    raw_cagr = (end_gdp / start_gdp) ** (1.0 / span) - 1.0
                    gdp_growth = min(0.06, max(0.015, raw_cagr))

    # Bottom-80% income share from latest survey observation (q1..q4).
    bottom_80 = fallback["bottom_80_income_share"]
    q_cols = [
        "income_share_q1",
        "income_share_q2",
        "income_share_q3",
        "income_share_q4",
    ]
    if all(col in country_df.columns for col in q_cols):
        q_df = country_df.dropna(subset=q_cols)
        if not q_df.empty:
            latest_q = q_df.iloc[-1]
            bottom_80 = float(sum(float(latest_q[col]) for col in q_cols))

    elec_use_kwh_pc = fallback["elec_use_kwh_pc"]
    if "elec_use_kwh_pc" in country_df.columns:
        kwh_df = country_df[
            country_df["elec_use_kwh_pc"].notna()
            & (country_df["year"] <= baseline_year)
        ]
        if not kwh_df.empty:
            elec_use_kwh_pc = float(kwh_df.iloc[-1]["elec_use_kwh_pc"])

    return SimulationMacroContext(
        iso3=iso3,
        baseline_year=baseline_year,
        rural_pop_share=rural_share,
        rural_pop_drift=rural_drift,
        gdp_per_capita_usd=gdp_pc,
        gdp_growth_rate=gdp_growth,
        bottom_80_income_share=bottom_80,
        elec_use_kwh_pc=elec_use_kwh_pc,
    )