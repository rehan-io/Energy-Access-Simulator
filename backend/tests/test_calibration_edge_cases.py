
import unittest
from unittest.mock import patch

import pandas as pd

from app.model.calibration import (
    get_country_inputs,
    calibrate_country_baseline,
)
from app.model.calibration_schema import CountryBaselineInputs


def make_dataset():
    """Create a small synthetic World Bank dataset."""

    rows = [
        ("population", 2024, 1000.0),
        ("population", 2025, 1100.0),
        ("rural_pop_share", 2024, 40.0),
        ("rural_pop_share", 2025, 50.0),
        ("elec_access_total", 2024, 60.0),
        ("elec_access_total", 2025, None),
        ("elec_access_rural", 2024, 20.0),
        ("elec_access_urban", 2024, 90.0),
        ("clean_cooking_access", 2024, 45.0),
        ("gdp_per_capita_usd", 2024, 2000.0),
    ]

    return pd.DataFrame(
        [
            {
                "country": "Testland",
                "iso3": "IND",
                "year": year,
                "indicator": indicator,
                "indicator_code": "TEST",
                "value": value,
                "retrieved_on": "2026-11-20",
            }
            for indicator, year, value in rows
        ]
    )


class TestCalibrationEdgeCases(unittest.TestCase):

    @patch("app.model.calibration.load_long_dataset")
    def test_latest_non_missing_observation_is_selected(self, mock_load):
        mock_load.return_value = make_dataset()

        inputs = get_country_inputs("IND")

        # 2025 population is available.
        self.assertEqual(inputs.population_total, 1100.0)
        self.assertEqual(inputs.observation_years["population"], 2025)

        # 2025 total electricity access is missing.
        # The valid 2024 observation must be selected.
        self.assertEqual(inputs.electricity_access_total_pct, 60.0)
        self.assertEqual(inputs.observation_years["elec_access_total"], 2024)

    @patch("app.model.calibration.load_long_dataset")
    def test_missing_rural_share_uses_documented_fallback(self, mock_load):
        df = make_dataset()
        df = df[df["indicator"] != "rural_pop_share"]
        mock_load.return_value = df

        inputs = get_country_inputs("IND")
        baseline = calibrate_country_baseline(inputs)

        self.assertEqual(baseline.population_rural, 550.0)
        self.assertTrue(
            any("assumed 50%" in warning
                for warning in baseline.calibration_warnings)
        )
        self.assertIn("rural_pop_share", baseline.missing_indicators)

    @patch("app.model.calibration.load_long_dataset")
    def test_missing_total_access_is_rejected(self, mock_load):
        df = make_dataset()
        df = df[df["indicator"] != "elec_access_total"]
        mock_load.return_value = df

        inputs = get_country_inputs("IND")

        with self.assertRaises(ValueError):
            calibrate_country_baseline(inputs)

    @patch("app.model.calibration.load_long_dataset")
    def test_rural_urban_discrepancy_generates_warning(self, mock_load):
        mock_load.return_value = make_dataset()

        inputs = get_country_inputs("IND")
        baseline = calibrate_country_baseline(inputs)

        self.assertTrue(
            any(
                "differs from reported total access" in warning
                for warning in baseline.calibration_warnings
            )
        )

    @patch("app.model.calibration.load_long_dataset")
    def test_population_counts_are_conserved(self, mock_load):
        mock_load.return_value = make_dataset()

        baseline = calibrate_country_baseline(
            get_country_inputs("IND")
        )

        self.assertAlmostEqual(
            baseline.population_rural + baseline.population_urban,
            baseline.population_total,
        )

        self.assertAlmostEqual(
            baseline.population_with_electricity
            + baseline.population_without_electricity,
            baseline.population_total,
        )

    def test_invalid_percentage_is_rejected(self):
        with self.assertRaises(ValueError):
            CountryBaselineInputs(
                iso3="IND",
                year=2025,
                population_total=1000,
                electricity_access_total_pct=120,
            )

    def test_negative_population_is_rejected(self):
        with self.assertRaises(ValueError):
            CountryBaselineInputs(
                iso3="IND",
                year=2025,
                population_total=-100,
            )


if __name__ == "__main__":
    unittest.main()
