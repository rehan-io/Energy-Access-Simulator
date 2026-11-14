
"""
Clean and transform raw World Bank indicator data.

Input:
    data/raw/worldbank/worldbank_long.csv

Outputs:
    data/processed/worldbank/worldbank_long.csv
    data/processed/worldbank/worldbank_wide.csv
    data/processed/worldbank/worldbank_latest.csv

"""

import argparse
from pathlib import Path

import pandas as pd

from app.data.schemas import LONG_COLUMNS, KEY_COLUMNS


def load_raw_data(input_path: Path) -> pd.DataFrame:
    """Load the raw long-format World Bank CSV."""

    if not input_path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found: {input_path}. "
            "Run fetch_worldbank.py first."
        )

    df = pd.read_csv(input_path)

    missing_columns = [
        column for column in LONG_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Raw dataset is missing columns: {missing_columns}"
        )

    return df.loc[:, LONG_COLUMNS].copy()


def normalise_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise fields and convert values to appropriate types."""

    df = df.copy()

    # Standardise text fields.
    text_columns = [
        "country",
        "iso3",
        "indicator_code",
        "indicator",
        "retrieved_on",
    ]

    for column in text_columns:
        df[column] = df[column].astype("string").str.strip()

    # Standardise ISO3 codes.
    df["iso3"] = df["iso3"].str.upper()

    # Convert year to integer.
    year = pd.to_numeric(df["year"], errors="coerce")

    if year.isna().any() or (year % 1 != 0).any():
        raise ValueError("Year column contains invalid values.")

    df["year"] = year.astype("int64")

    # Convert indicator values to numeric.
    original_values = df["value"]
    numeric_values = pd.to_numeric(
        original_values,
        errors="coerce",
    )

    # Distinguish genuine missing values from malformed strings.
    malformed = (
        original_values.notna()
        & original_values.astype("string").str.strip().ne("")
        & numeric_values.isna()
    )

    if malformed.any():
        raise ValueError(
            "Indicator values contain non-numeric entries."
        )

    df["value"] = numeric_values.astype("float64")

    # Standardise retrieval dates.
    retrieved_dates = pd.to_datetime(
        df["retrieved_on"],
        errors="coerce",
    )

    if retrieved_dates.isna().any():
        raise ValueError("Invalid retrieved_on dates found.")

    df["retrieved_on"] = retrieved_dates.dt.strftime("%Y-%m-%d")

    # Reject missing identifiers.
    identifier_columns = [
        "country",
        "iso3",
        "indicator_code",
        "indicator",
    ]

    if df[identifier_columns].isna().any().any():
        raise ValueError("Missing country or indicator identifiers.")

    if (df[identifier_columns] == "").any().any():
        raise ValueError("Empty country or indicator identifiers.")

    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate observations.

    Exact duplicates are removed first.

    If the same country/year/indicator was retrieved multiple times,
    the most recently retrieved observation is retained.

    Conflicting values from the same retrieval date are rejected.
    """

    df = df.drop_duplicates().copy()

    duplicate_mask = df.duplicated(
        subset=list(KEY_COLUMNS),
        keep=False,
    )

    if duplicate_mask.any():
        duplicates = df.loc[duplicate_mask]

        for key, group in duplicates.groupby(
            list(KEY_COLUMNS),
            dropna=False,
        ):
            latest_date = group["retrieved_on"].max()

            latest_group = group.loc[
                group["retrieved_on"] == latest_date
            ]

            distinct_values = (
                latest_group["value"]
                .dropna()
                .unique()
            )

            if len(distinct_values) > 1:
                raise ValueError(
                    "Conflicting values found for "
                    f"{key} on {latest_date}."
                )

    # Prefer the newest retrieval date.
    # If the date is identical, prefer a non-missing observation.
    df = df.sort_values(
        ["retrieved_on", "value"],
        na_position="first",
    )

    df = df.drop_duplicates(
        subset=list(KEY_COLUMNS),
        keep="last",
    )

    return df.sort_values(
        ["iso3", "indicator", "year"]
    ).reset_index(drop=True)


def create_wide_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert long-format data into one row per country and year.

    Each indicator becomes a separate column.
    Missing values are not filled or interpolated.
    """

    wide = df.pivot(
        index=["country", "iso3", "year"],
        columns="indicator",
        values="value",
    ).reset_index()

    wide.columns.name = None

    return wide.sort_values(
        ["iso3", "year"]
    ).reset_index(drop=True)


def create_latest_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Select the latest non-missing observation for each
    country and indicator independently.

    Different indicators may have different observation years.
    """

    observed = df.loc[df["value"].notna()].copy()

    if observed.empty:
        return observed.reset_index(drop=True)

    latest_year = observed.groupby(
        ["iso3", "indicator"]
    )["year"].transform("max")

    latest = observed.loc[
        observed["year"] == latest_year
    ].copy()

    return latest.sort_values(
        ["iso3", "indicator"]
    ).reset_index(drop=True)


def clean_worldbank_data(
    input_path: Path,
    output_dir: Path,
) -> None:
    """Execute the complete cleaning and transformation pipeline."""

    print("Loading raw World Bank dataset...")

    raw = load_raw_data(input_path)

    print(f"Loaded {len(raw)} raw observations.")

    print("Normalising data...")

    cleaned = normalise_data(raw)

    print("Removing duplicate observations...")

    cleaned = remove_duplicates(cleaned)

    print("Generating transformed datasets...")

    wide = create_wide_dataset(cleaned)
    latest = create_latest_dataset(cleaned)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    cleaned.to_csv(
        output_dir / "worldbank_long.csv",
        index=False,
    )

    wide.to_csv(
        output_dir / "worldbank_wide.csv",
        index=False,
    )

    latest.to_csv(
        output_dir / "worldbank_latest.csv",
        index=False,
    )

    print("\nCleaning completed successfully.")

    print(f"Clean observations: {len(cleaned)}")
    print(f"Wide-format rows: {len(wide)}")
    print(f"Latest observations: {len(latest)}")

    print(f"\nOutput directory: {output_dir.resolve()}")


def main():
    parser = argparse.ArgumentParser(
        description="Clean World Bank indicator data."
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/worldbank/worldbank_long.csv"),
        help="Path to raw World Bank long-format CSV.",
    )

    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("data/processed/worldbank"),
        help="Directory for cleaned datasets.",
    )

    args = parser.parse_args()

    clean_worldbank_data(
        input_path=args.input,
        output_dir=args.outdir,
    )


if __name__ == "__main__":
    main()
