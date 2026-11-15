
"""Unit tests for the World Bank cleaning and validation pipeline."""

import unittest

import pandas as pd

from app.data.schemas import LONG_COLUMNS
from app.data.clean_worldbank import (
    normalise_data,
    remove_duplicates,
    create_wide_dataset,
    create_latest_dataset,
)
from app.data.validate_worldbank import validate_worldbank_data


def make_row(
    country="India",
    iso3="IND",
    year=2022,
    indicator="elec_access_total",
    indicator_code="EG.ELC.ACCS.ZS",
    value=95.0,
    retrieved_on="2026-11-15",
):
    """Create one synthetic World Bank observation."""

    return {
        "country": country,
        "iso3": iso3,
        "year": year,
        "indicator_code": indicator_code,
        "indicator": indicator,
        "value": value,
        "retrieved_on": retrieved_on,
    }


def make_dataframe(rows=None):
    """Create a DataFrame with the expected long-format schema."""

    if rows is None:
        rows = [
            make_row(),
            make_row(
                year=2023,
                value=96.0,
                retrieved_on="2026-11-15",
            ),
            make_row(
                year=2022,
                indicator="population",
                indicator_code="SP.POP.TOTL",
                value=1400000000,
            ),
        ]

    return pd.DataFrame(rows, columns=LONG_COLUMNS)


class TestWorldBankCleaning(unittest.TestCase):

    def test_normalise_data_converts_types(self):
        """Years and values should become numeric; text should be normalized."""

        df = make_dataframe([
            make_row(
                iso3=" ind ",
                year="2022",
                value="95.5",
            )
        ])

        cleaned = normalise_data(df)

        self.assertEqual(cleaned.loc[0, "iso3"], "IND")
        self.assertEqual(cleaned.loc[0, "year"], 2022)
        self.assertEqual(cleaned.loc[0, "value"], 95.5)
        self.assertEqual(
            str(cleaned["year"].dtype),
            "int64",
        )

    def test_normalise_data_rejects_invalid_year(self):
        df = make_dataframe([
            make_row(year="not-a-year")
        ])

        with self.assertRaises(ValueError):
            normalise_data(df)

    def test_normalise_data_rejects_non_numeric_value(self):
        df = make_dataframe([
            make_row(value="not-numeric")
        ])

        with self.assertRaises(ValueError):
            normalise_data(df)

    def test_remove_duplicates_keeps_latest_retrieval(self):
        """The most recently retrieved observation should be retained."""

        df = make_dataframe([
            make_row(
                value=90.0,
                retrieved_on="2026-01-01",
            ),
            make_row(
                value=95.0,
                retrieved_on="2026-11-15",
            ),
        ])

        cleaned = remove_duplicates(df)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned.iloc[0]["value"], 95.0)

    def test_remove_duplicates_rejects_conflicting_same_date(self):
        """Conflicting values retrieved on the same date should fail."""

        df = make_dataframe([
            make_row(value=90.0),
            make_row(value=95.0),
        ])

        with self.assertRaises(ValueError):
            remove_duplicates(df)

    def test_create_wide_dataset(self):
        """Indicators should become separate columns."""

        df = make_dataframe()
        wide = create_wide_dataset(df)

        self.assertIn("elec_access_total", wide.columns)
        self.assertIn("population", wide.columns)
        self.assertEqual(len(wide), 2)

    def test_create_latest_dataset(self):
        """Latest observations should be selected independently per indicator."""

        df = make_dataframe([
            make_row(
                year=2020,
                value=90.0,
            ),
            make_row(
                year=2022,
                value=95.0,
            ),
            make_row(
                year=2019,
                indicator="population",
                indicator_code="SP.POP.TOTL",
                value=1300000000,
            ),
        ])

        latest = create_latest_dataset(df)

        access = latest.loc[
            latest["indicator"] == "elec_access_total"
        ]

        population = latest.loc[
            latest["indicator"] == "population"
        ]

        self.assertEqual(access.iloc[0]["year"], 2022)
        self.assertEqual(population.iloc[0]["year"], 2019)


class TestWorldBankValidation(unittest.TestCase):

    def test_valid_dataset_passes(self):
        df = make_dataframe()

        result = validate_worldbank_data(df)

        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)

    def test_missing_values_generate_warning(self):
        df = make_dataframe([
            make_row(value=None)
        ])

        result = validate_worldbank_data(df)

        self.assertTrue(result.is_valid)
        self.assertTrue(
            any("missing indicator values" in warning
                for warning in result.warnings)
        )

    def test_percentage_above_100_is_rejected(self):
        df = make_dataframe([
            make_row(value=105.0)
        ])

        result = validate_worldbank_data(df)

        self.assertFalse(result.is_valid)
        self.assertTrue(
            any("Percentage values outside" in error
                for error in result.errors)
        )

    def test_negative_non_negative_indicator_is_rejected(self):
        df = make_dataframe([
            make_row(
                indicator="population",
                indicator_code="SP.POP.TOTL",
                value=-100,
            )
        ])

        result = validate_worldbank_data(df)

        self.assertFalse(result.is_valid)
        self.assertTrue(
            any("Negative values" in error
                for error in result.errors)
        )

    def test_unknown_indicator_is_rejected(self):
        df = make_dataframe([
            make_row(
                indicator="unknown_indicator",
                indicator_code="UNKNOWN",
            )
        ])

        result = validate_worldbank_data(df)

        self.assertFalse(result.is_valid)
        self.assertTrue(
            any("Unknown indicators" in error
                for error in result.errors)
        )

    def test_duplicate_keys_are_rejected(self):
        df = make_dataframe([
            make_row(value=90.0),
            make_row(value=90.0),
        ])

        result = validate_worldbank_data(df)

        self.assertFalse(result.is_valid)
        self.assertTrue(
            any("Duplicate country-year-indicator keys" in error
                for error in result.errors)
        )


if __name__ == "__main__":
    unittest.main()
