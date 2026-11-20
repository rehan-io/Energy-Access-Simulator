import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.model import simulation_inputs


client = TestClient(app)


def fake_simulation(country_code, years=25, trend_window=10,
                    policy_adjustments=None, data_dir=None):

    indicators = [
        "elec_access_total",
        "elec_access_rural",
        "elec_access_urban",
        "clean_cooking_access",
    ]

    base = {
        "IND": 90.0,
        "KEN": 70.0,
        "RWA": 60.0,
        "NGA": 50.0,
    }[country_code]

    historical = {
        "year": 2024,
        "kind": "historical",
        "elec_access_total": base,
        "elec_access_rural": base - 5,
        "elec_access_urban": base + 5,
        "clean_cooking_access": base - 10,
    }

    projected = {
        "year": 2025,
        "kind": "projected",
        "elec_access_total": min(100, base + 1),
        "elec_access_rural": min(100, base - 4),
        "elec_access_urban": min(100, base + 6),
        "clean_cooking_access": min(100, base - 9),
    }

    return {
        "countryCode": country_code,
        "baselineYear": 2024,
        "trendWindow": trend_window,
        "trends": {
            indicator: {
                "latest_year": 2024,
                "latest_value": historical[indicator],
                "annual_trend": 1.0,
                "observations_used": 10,
                "window": trend_window,
                "first_year_used": 2015,
                "last_year_used": 2024,
            }
            for indicator in indicators
        },
        "policyAdjustments": policy_adjustments or {},
        "history": [historical] + [
            {
                **projected,
                "year": 2024 + i,
            }
            for i in range(1, years + 1)
        ],
    }


@pytest.fixture
def mocked_simulation(monkeypatch):
    monkeypatch.setattr(
        "app.main.run_country_access_simulation",
        fake_simulation,
    )


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_simulation_endpoint(mocked_simulation):
    response = client.post(
        "/api/simulate",
        json={
            "country": "IND",
            "years": 5,
            "trendWindow": 10,
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["countryCode"] == "IND"
    assert result["baselineYear"] == 2024

    projected = [
        row for row in result["history"]
        if row["kind"] == "projected"
    ]

    assert len(projected) == 5


def test_simulation_uses_selected_country(mocked_simulation):
    india = client.post(
        "/api/simulate",
        json={"country": "IND", "years": 1},
    ).json()

    kenya = client.post(
        "/api/simulate",
        json={"country": "KEN", "years": 1},
    ).json()

    assert (
        india["history"][0]["elec_access_total"]
        != kenya["history"][0]["elec_access_total"]
    )


def test_rejects_unsupported_country(mocked_simulation):
    response = client.post(
        "/api/simulate",
        json={"country": "USA"},
    )

    assert response.status_code == 404


def test_rejects_invalid_horizon():
    response = client.post(
        "/api/simulate",
        json={"country": "IND", "years": 0},
    )

    assert response.status_code == 422


def test_rejects_unknown_policy_indicator(mocked_simulation):
    response = client.post(
        "/api/simulate",
        json={
            "country": "IND",
            "policyAdjustments": {
                "solar_panel_share": 2.0,
            },
        },
    )

    assert response.status_code == 422


def test_accepts_valid_policy_adjustment(mocked_simulation):
    response = client.post(
        "/api/simulate",
        json={
            "country": "IND",
            "years": 2,
            "policyAdjustments": {
                "elec_access_rural": 0.5,
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["policyAdjustments"]["elec_access_rural"] == 0.5


def test_baseline_endpoint(mocked_simulation):
    response = client.get("/api/baseline/IND")

    assert response.status_code == 200

    result = response.json()

    assert result["countryCode"] == "IND"
    assert result["baselineYear"] == 2024
    assert len(result["trends"]) == 4
    assert all(
        row["kind"] == "historical"
        for row in result["historical"]
    )


def test_countries_endpoint(mocked_simulation):
    response = client.get("/api/countries")

    assert response.status_code == 200

    countries = response.json()

    assert len(countries) == 4
    assert {country["code"] for country in countries} == {
        "IND", "KEN", "RWA", "NGA"
    }

    assert all("access" in country for country in countries)
    assert all("baselineYear" in country for country in countries)