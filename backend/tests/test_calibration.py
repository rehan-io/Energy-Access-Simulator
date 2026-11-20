
import unittest

from app.model.calibration import (
    get_country_inputs,
    calibrate_country_baseline,
    get_calibrated_baseline,
)


DATA_DIR = (
    r"D:\Users\Shubhankar\CS 699 Proj\files\data\processed\worldbank"
)


class TestCountryCalibration(unittest.TestCase):

    def test_all_supported_countries_calibrate(self):
        for country in ("IND", "KEN", "RWA", "NGA"):
            with self.subTest(country=country):
                baseline = get_calibrated_baseline(country, DATA_DIR)

                self.assertEqual(baseline.iso3, country)
                self.assertGreater(baseline.population_total, 0)
                self.assertGreaterEqual(baseline.electricity_access_rate, 0)
                self.assertLessEqual(baseline.electricity_access_rate, 1)

    def test_population_is_conserved(self):
        baseline = get_calibrated_baseline("IND", DATA_DIR)

        self.assertAlmostEqual(
            baseline.population_rural + baseline.population_urban,
            baseline.population_total,
            places=4,
        )

        self.assertAlmostEqual(
            baseline.population_with_electricity
            + baseline.population_without_electricity,
            baseline.population_total,
            places=4,
        )

    def test_latest_non_missing_observations_are_selected(self):
        inputs = get_country_inputs("IND", DATA_DIR)

        self.assertEqual(inputs.observation_years["elec_access_total"], 2024)
        self.assertEqual(inputs.observation_years["population"], 2025)

    def test_unknown_country_is_rejected(self):
        with self.assertRaises(ValueError):
            get_country_inputs("USA", DATA_DIR)

    def test_missing_total_access_is_rejected(self):
        inputs = get_country_inputs("IND", DATA_DIR)

        from dataclasses import replace

        incomplete = replace(
            inputs,
            electricity_access_total_pct=None,
        )

        with self.assertRaises(ValueError):
            calibrate_country_baseline(incomplete)


if __name__ == "__main__":
    unittest.main()
