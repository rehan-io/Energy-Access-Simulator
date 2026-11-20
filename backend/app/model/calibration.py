
"""Build country-level simulation baselines from World Bank data."""

from app.data.dataset_loader import load_long_dataset
from app.model.calibration_schema import (
    CountryBaselineInputs,
    CalibratedCountryBaseline,
)


INDICATOR_FIELDS = {
    "population": "population_total",
    "rural_pop_share": "population_rural_pct",
    "elec_access_total": "electricity_access_total_pct",
    "elec_access_rural": "electricity_access_rural_pct",
    "elec_access_urban": "electricity_access_urban_pct",
    "clean_cooking_access": "clean_cooking_access_pct",
    "gdp_per_capita_usd": "gdp_per_capita_usd",
}

COUNTRY_NAMES = {
    "IND": "India",
    "KEN": "Kenya",
    "RWA": "Rwanda",
    "NGA": "Nigeria",
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
        gdp_per_capita_usd=inputs.gdp_per_capita_usd,
        observation_years=inputs.observation_years,
        missing_indicators=tuple(missing),
        calibration_warnings=tuple(warnings),
    )


def get_calibrated_baseline(country_code: str, data_dir=None):
    """Convenience function for loading and calibrating a country."""

    inputs = get_country_inputs(country_code, data_dir)
    return calibrate_country_baseline(inputs)
