
import unittest

from app.core.access_simulation import (
    ACCESS_INDICATORS,
    estimate_annual_trend,
    run_access_simulation,
)


def make_history():
    return {
        indicator: [
            {"year": year, "value": 40.0 + (year - 2015) * 2.0}
            for year in range(2015, 2025)
        ]
        for indicator in ACCESS_INDICATORS
    }


class TestTrendEstimation(unittest.TestCase):

    def test_linear_trend_is_recovered(self):
        observations = [
            {"year": year, "value": 20 + 3 * (year - 2010)}
            for year in range(2010, 2020)
        ]

        result = estimate_annual_trend(observations)

        self.assertAlmostEqual(result["annual_trend"], 3.0)
        self.assertEqual(result["observations_used"], 10)

    def test_missing_values_are_ignored(self):
        observations = [
            {"year": 2018, "value": 20.0},
            {"year": 2019, "value": None},
            {"year": 2020, "value": 24.0},
        ]

        result = estimate_annual_trend(observations)

        self.assertEqual(result["observations_used"], 2)
        self.assertAlmostEqual(result["annual_trend"], 2.0)

    def test_actual_calendar_years_are_used(self):
        observations = [
            {"year": 2010, "value": 20.0},
            {"year": 2012, "value": 24.0},
        ]

        result = estimate_annual_trend(observations)

        self.assertAlmostEqual(result["annual_trend"], 2.0)

    def test_duplicate_years_are_rejected(self):
        observations = [
            {"year": 2020, "value": 20.0},
            {"year": 2020, "value": 21.0},
        ]

        with self.assertRaises(ValueError):
            estimate_annual_trend(observations)

    def test_invalid_percentages_are_rejected(self):
        with self.assertRaises(ValueError):
            estimate_annual_trend([
                {"year": 2020, "value": 120.0},
                {"year": 2021, "value": 121.0},
            ])


class TestAccessSimulation(unittest.TestCase):

    def test_all_indicators_are_projected(self):
        result = run_access_simulation(make_history(), years=5)

        projected = [
            row for row in result["history"]
            if row["kind"] == "projected"
        ]

        self.assertEqual(len(projected), 5)

        for row in projected:
            for indicator in ACCESS_INDICATORS:
                self.assertIsNotNone(row[indicator])
                self.assertGreaterEqual(row[indicator], 0)
                self.assertLessEqual(row[indicator], 100)

    def test_indicators_are_projected_independently(self):
        result = run_access_simulation(make_history(), years=1)

        projected = result["history"][-1]

        self.assertAlmostEqual(
            projected["elec_access_total"],
            60.0,
        )

    def test_policy_adjustment_changes_only_targeted_indicator(self):
        baseline = run_access_simulation(make_history(), years=1)

        scenario = run_access_simulation(
            make_history(),
            years=1,
            policy_adjustments={"clean_cooking_access": 1.0},
        )

        base_row = baseline["history"][-1]
        scenario_row = scenario["history"][-1]

        self.assertAlmostEqual(
            scenario_row["clean_cooking_access"]
            - base_row["clean_cooking_access"],
            1.0,
        )

        self.assertAlmostEqual(
            scenario_row["elec_access_total"],
            base_row["elec_access_total"],
        )

    def test_projection_is_bounded_at_100(self):
        data = make_history()

        for indicator in ACCESS_INDICATORS:
            data[indicator] = [
                {"year": 2023, "value": 99.0},
                {"year": 2024, "value": 100.0},
            ]

        result = run_access_simulation(data, years=3)

        for row in result["history"]:
            if row["kind"] == "projected":
                for indicator in ACCESS_INDICATORS:
                    self.assertLessEqual(row[indicator], 100.0)

    def test_unknown_policy_indicator_is_rejected(self):
        with self.assertRaises(ValueError):
            run_access_simulation(
                make_history(),
                policy_adjustments={"grid_share": 1.0},
            )

    def test_missing_required_indicator_is_rejected(self):
        data = make_history()
        del data["elec_access_rural"]

        with self.assertRaises(ValueError):
            run_access_simulation(data)

    def test_empty_future_historical_year_is_excluded(self):
         historical_data = make_history()

         for indicator in ACCESS_INDICATORS:
            historical_data[indicator].append({
                "year": 2025,
                "value": None,
            })

         result = run_access_simulation(
            historical_data,
            years=5,
         )

         rows_2025 = [
            row for row in result["history"]
            if row["year"] == 2025
        ]

         self.assertEqual(len(rows_2025), 1)
         self.assertEqual(rows_2025[0]["kind"], "projected")
    
    def test_valid_observation_survives_null_duplicate(self):
        data = make_history()

        data["elec_access_total"].extend([
            {"year": 2024, "value": None},
            {"year": 2024, "value": 58.0},
        ])

        result = run_access_simulation(data, years=1)

        row = next(
            row for row in result["history"]
            if row["year"] == 2024
        )

        self.assertEqual(row["elec_access_total"], 58.0)

    def test_identical_valid_duplicates_are_accepted(self):
        data = make_history()

        data["elec_access_total"].append({
            "year": 2024,
            "value": 58.0,
        })

        result = run_access_simulation(data, years=1)

        row = next(
            row for row in result["history"]
            if row["year"] == 2024
        )

        self.assertEqual(row["elec_access_total"], 58.0)

    def test_conflicting_valid_duplicates_are_rejected(self):
        data = make_history()

        data["elec_access_total"].append({
            "year": 2024,
            "value": 59.0,
        })

        with self.assertRaises(ValueError):
            run_access_simulation(data, years=1)

if __name__ == "__main__":
    unittest.main()
