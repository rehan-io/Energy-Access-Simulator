import pandas as pd
import pytest

from app.core.access_simulation import ACCESS_INDICATORS
from app.model import simulation_inputs


def make_dataset():
    rows = []

    for indicator in ACCESS_INDICATORS:
        for year in range(2020, 2025):
            rows.append({
                "iso3": "IND",
                "indicator": indicator,
                "year": year,
                "value": 50.0 + (year - 2020),
            })

            rows.append({
                "iso3": "KEN",
                "indicator": indicator,
                "year": year,
                "value": 30.0 + (year - 2020),
            })

    # An explicitly missing observation must remain missing.
    rows.append({
        "iso3": "IND",
        "indicator": "elec_access_rural",
        "year": 2025,
        "value": float("nan"),
    })

    return pd.DataFrame(rows)


@pytest.fixture
def mocked_dataset(monkeypatch):
    dataset = make_dataset()

    monkeypatch.setattr(
        simulation_inputs,
        "load_long_dataset",
        lambda data_dir=None: dataset,
    )

    return dataset


def test_loads_all_required_indicators(mocked_dataset):
    result = simulation_inputs.load_country_historical_data("IND")

    assert set(result.keys()) == set(ACCESS_INDICATORS)

    for indicator in ACCESS_INDICATORS:
        assert len(result[indicator]) > 0


def test_country_data_is_not_mixed(mocked_dataset):
    india = simulation_inputs.load_country_historical_data("IND")
    kenya = simulation_inputs.load_country_historical_data("KEN")

    assert india["elec_access_total"][-1]["value"] == 54.0
    assert kenya["elec_access_total"][-1]["value"] == 34.0


def test_preserves_missing_values(mocked_dataset):
    result = simulation_inputs.load_country_historical_data("IND")

    rural_observations = result["elec_access_rural"]

    assert rural_observations[-1]["year"] == 2025
    assert rural_observations[-1]["value"] is None


def test_preserves_actual_observation_years(mocked_dataset):
    result = simulation_inputs.load_country_historical_data("IND")

    years = [
        observation["year"]
        for observation in result["elec_access_total"]
    ]

    assert years == [2020, 2021, 2022, 2023, 2024]


def test_country_code_is_case_insensitive(mocked_dataset):
    upper = simulation_inputs.load_country_historical_data("IND")
    lower = simulation_inputs.load_country_historical_data("ind")

    assert upper == lower


def test_unknown_country_raises_error(mocked_dataset):
    with pytest.raises(ValueError, match="No processed World Bank"):
        simulation_inputs.load_country_historical_data("XXX")


def test_missing_indicator_raises_error(mocked_dataset, monkeypatch):
    dataset = mocked_dataset[
        mocked_dataset["indicator"] != "clean_cooking_access"
    ]

    monkeypatch.setattr(
        simulation_inputs,
        "load_long_dataset",
        lambda data_dir=None: dataset,
    )

    with pytest.raises(ValueError, match="clean_cooking_access"):
        simulation_inputs.load_country_historical_data("IND")
def test_country_wrapper_runs_simulation(mocked_dataset):
    result = simulation_inputs.run_country_access_simulation(
        country_code="IND",
        years=5,
    )

    assert result["countryCode"] == "IND"
    assert result["baselineYear"] == 2024
    assert len(result["history"]) > 0

    projected = [
        row for row in result["history"]
        if row["kind"] == "projected"
    ]

    assert len(projected) == 5


def test_country_wrapper_uses_selected_country(mocked_dataset):
    india = simulation_inputs.run_country_access_simulation(
        "IND",
        years=2,
    )
    kenya = simulation_inputs.run_country_access_simulation(
        "KEN",
        years=2,
    )

    india_first = next(
        row for row in india["history"]
        if row["kind"] == "projected"
    )
    kenya_first = next(
        row for row in kenya["history"]
        if row["kind"] == "projected"
    )

    assert india_first["elec_access_total"] != (
        kenya_first["elec_access_total"]
    )