import unittest
from fastapi.testclient import TestClient

from app.core.simulation import run_coupled_simulation
from app.main import app
from app.model.calibration import get_simulation_macro_context
from app.model.simulation_inputs import run_country_coupled_simulation


client = TestClient(app)


class TestCoupledSimulationFormula(unittest.TestCase):

    def test_kenya_year0_baseline_and_subsidy_grid_match_benchmarks(self):
        macro = get_simulation_macro_context("KEN", baseline_year=2024)

        baseline = run_coupled_simulation(
            country="KEN",
            baseline_year=2024,
            years=1,
            elec_total_pct=77.0,
            elec_rural_pct=67.1,
            elec_urban_pct=98.1,
            clean_cooking_pct=32.0,
            macro=macro,
        )
        gain_base = baseline["projected"][0]["elec_access_rural"] - 67.1
        self.assertAlmostEqual(gain_base, 1.66, places=1)

        boosted = run_coupled_simulation(
            country="KEN",
            baseline_year=2024,
            years=1,
            elec_total_pct=77.0,
            elec_rural_pct=67.1,
            elec_urban_pct=98.1,
            clean_cooking_pct=32.0,
            macro=macro,
            subsidy=70.0,
            grid_ext=70.0,
        )
        gain_boosted = boosted["projected"][0]["elec_access_rural"] - 67.1
        self.assertAlmostEqual(gain_boosted, 4.65, places=1)

    def test_india_clean_cooking_stacking_and_subsidy(self):
        macro = get_simulation_macro_context("IND", baseline_year=2024)

        baseline = run_coupled_simulation(
            country="IND",
            baseline_year=2024,
            years=1,
            elec_total_pct=99.9,
            elec_rural_pct=99.9,
            elec_urban_pct=100.0,
            clean_cooking_pct=81.0,
            macro=macro,
        )
        self.assertAlmostEqual(
            baseline["projected"][0]["clean_cooking_access"] - 81.0,
            1.31,
            places=1,
        )

        subsidized = run_coupled_simulation(
            country="IND",
            baseline_year=2024,
            years=1,
            elec_total_pct=99.9,
            elec_rural_pct=99.9,
            elec_urban_pct=100.0,
            clean_cooking_pct=81.0,
            macro=macro,
            subsidy=70.0,
        )
        self.assertAlmostEqual(
            subsidized["projected"][0]["clean_cooking_access"] - 81.0,
            2.48,
            places=1,
        )

    def test_rwanda_uncompensated_carbon_tax_vs_shielded(self):
        macro = get_simulation_macro_context("RWA", baseline_year=2024)

        base = run_coupled_simulation(
            country="RWA",
            baseline_year=2024,
            years=1,
            elec_total_pct=72.0,
            elec_rural_pct=65.2,
            elec_urban_pct=88.0,
            clean_cooking_pct=9.0,
            macro=macro,
            recycle_tax_revenue=False,
        )
        uncomp_tax = run_coupled_simulation(
            country="RWA",
            baseline_year=2024,
            years=1,
            elec_total_pct=72.0,
            elec_rural_pct=65.2,
            elec_urban_pct=88.0,
            clean_cooking_pct=9.0,
            macro=macro,
            carbon_tax=70.0,
            recycle_tax_revenue=False,
        )
        shielded_tax = run_coupled_simulation(
            country="RWA",
            baseline_year=2024,
            years=1,
            elec_total_pct=72.0,
            elec_rural_pct=65.2,
            elec_urban_pct=88.0,
            clean_cooking_pct=9.0,
            macro=macro,
            subsidy=70.0,
            carbon_tax=70.0,
            recycle_tax_revenue=False,
        )
        recycled_only = run_coupled_simulation(
            country="RWA",
            baseline_year=2024,
            years=1,
            elec_total_pct=72.0,
            elec_rural_pct=65.2,
            elec_urban_pct=88.0,
            clean_cooking_pct=9.0,
            macro=macro,
            carbon_tax=70.0,
            recycle_tax_revenue=True,
        )

        c_base = base["projected"][0]["clean_cooking_access"]
        c_uncomp = uncomp_tax["projected"][0]["clean_cooking_access"]
        c_shielded = shielded_tax["projected"][0]["clean_cooking_access"]
        c_recycled = recycled_only["projected"][0]["clean_cooking_access"]

        self.assertLess(c_uncomp, c_base)
        self.assertGreater(c_recycled, c_base)
        self.assertGreater(c_shielded, c_recycled)

    def test_bounds_and_five_tier_stock_conservation(self):
        for iso3 in ("IND", "KEN", "RWA", "NGA"):
            result = run_country_coupled_simulation(
                country_code=iso3,
                years=30,
                policy_levers={
                    "subsidy": 100.0,
                    "carbon_tax": 100.0,
                    "off_grid": 100.0,
                    "grid_ext": 100.0,
                    "recycle_tax_revenue": True,
                },
            )
            projected = [
                row for row in result["history"] if row["kind"] == "projected"
            ]
            self.assertEqual(len(projected), 30)

            for row in projected:
                for key in (
                    "elec_access_total",
                    "elec_access_rural",
                    "elec_access_urban",
                    "clean_cooking_access",
                    "traditional",
                    "lantern",
                    "shs",
                    "minigrid",
                    "grid",
                ):
                    self.assertGreaterEqual(row[key], 0.0)
                    self.assertLessEqual(row[key], 100.0)

                tier_sum = (
                    row["traditional"]
                    + row["lantern"]
                    + row["shs"]
                    + row["minigrid"]
                    + row["grid"]
                )
                self.assertAlmostEqual(tier_sum, 100.0, places=2)
                self.assertAlmostEqual(
                    100.0 - row["traditional"],
                    row["elec_access_total"],
                    places=2,
                )

    def test_api_simulate_accepts_policy_levers(self):
        response = client.post(
            "/api/simulate",
            json={
                "country": "KEN",
                "years": 10,
                "trendWindow": 10,
                "policyLevers": {
                    "subsidy": 60,
                    "carbon_tax": 40,
                    "off_grid": 55,
                    "grid_ext": 50,
                    "recycle_tax_revenue": True,
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["modelMode"], "coupled")
        projected = [r for r in body["history"] if r["kind"] == "projected"]
        self.assertEqual(len(projected), 10)
        self.assertIn("grid", projected[0])
        self.assertIn("shs", projected[0])


if __name__ == "__main__":
    unittest.main()