
"""
Validate cleaned World Bank indicator data and generate a quality report.

Run from the backend directory:

    python -m app.data.validate_worldbank

Or specify a dataset and report path:

    python -m app.data.validate_worldbank \
        --input ../files/data/processed/worldbank/worldbank_long.csv \
        --report ../files/data/processed/worldbank/worldbank_quality_report.txt
"""

import argparse
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from app.data.schemas import (
    INDICATOR_CODES,
    KEY_COLUMNS,
    LONG_COLUMNS,
    NON_NEGATIVE_INDICATORS,
    PERCENTAGE_INDICATORS,
)


@dataclass
class ValidationResult:
    """Stores validation findings and dataset coverage information."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def validate_worldbank_data(df: pd.DataFrame) -> ValidationResult:
    """Run structural, identifier, range, and duplicate checks."""

    result = ValidationResult()

    # 1. Schema validation
    missing_columns = [
        column for column in LONG_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        result.errors.append(
            f"Missing required columns: {missing_columns}"
        )
        return result

    data = df.copy()

    # 2. Empty dataset check
    if data.empty:
        result.errors.append("Dataset contains no observations.")
        return result

    result.summary["total_rows"] = len(data)

    # 3. Missing and empty identifiers
    identifier_columns = [
        "country",
        "iso3",
        "indicator_code",
        "indicator",
    ]

    for column in identifier_columns:
        missing_count = data[column].isna().sum()

        empty_count = (
            data[column]
            .astype("string")
            .str.strip()
            .eq("")
            .sum()
        )

        count = int(missing_count + empty_count)

        if count:
            result.errors.append(
                f"{column}: {count} missing or empty values."
            )

    # Stop identifier-dependent checks if identifiers are unusable.
    if data[identifier_columns].isna().any().any():
        return result

    # 4. Country code validation
    iso3 = data["iso3"].astype("string").str.strip().str.upper()

    invalid_iso3 = ~iso3.str.fullmatch(r"[A-Z]{3}", na=False)

    if invalid_iso3.any():
        result.errors.append(
            f"Invalid ISO3 country codes: {int(invalid_iso3.sum())} rows."
        )

    # 5. Indicator name and code consistency
    expected_codes = data["indicator"].map(INDICATOR_CODES)

    unknown_indicators = expected_codes.isna()

    if unknown_indicators.any():
        names = sorted(
            data.loc[unknown_indicators, "indicator"]
            .astype(str)
            .unique()
        )
        result.errors.append(
            f"Unknown indicators found: {names}"
        )

    known = ~unknown_indicators

    mismatched_codes = (
        data.loc[known, "indicator_code"].astype(str).str.strip()
        != expected_codes.loc[known].astype(str)
    )

    if mismatched_codes.any():
        result.errors.append(
            f"Indicator name/code mismatches: "
            f"{int(mismatched_codes.sum())} rows."
        )

    # 6. Year validation
    years = pd.to_numeric(data["year"], errors="coerce")

    invalid_years = (
        years.isna()
        | (years % 1 != 0)
        | (years < 1900)
    )

    if invalid_years.any():
        result.errors.append(
            f"Invalid year values: {int(invalid_years.sum())} rows."
        )

    # 7. Numeric value validation
    values = pd.to_numeric(data["value"], errors="coerce")

    malformed_values = data["value"].notna() & values.isna()

    if malformed_values.any():
        result.errors.append(
            f"Non-numeric indicator values: "
            f"{int(malformed_values.sum())} rows."
        )

    missing_values = int(values.isna().sum())

    if missing_values:
        result.warnings.append(
            f"{missing_values} observations have missing indicator values."
        )

    # 8. Non-negative values
    indicator_names = data["indicator"].astype(str)

    non_negative_mask = indicator_names.isin(
        NON_NEGATIVE_INDICATORS
    )

    negative_values = (
        non_negative_mask
        & values.notna()
        & (values < 0)
    )

    if negative_values.any():
        result.errors.append(
            f"Negative values found in non-negative indicators: "
            f"{int(negative_values.sum())} rows."
        )

    # 9. Percentage ranges
    percentage_mask = indicator_names.isin(
        PERCENTAGE_INDICATORS
    )

    invalid_percentages = (
        percentage_mask
        & values.notna()
        & ((values < 0) | (values > 100))
    )

    if invalid_percentages.any():
        result.errors.append(
            f"Percentage values outside [0, 100]: "
            f"{int(invalid_percentages.sum())} rows."
        )

    # 10. Duplicate observations
    duplicate_mask = data.duplicated(
        subset=list(KEY_COLUMNS),
        keep=False,
    )

    if duplicate_mask.any():
        result.errors.append(
            f"Duplicate country-year-indicator keys: "
            f"{int(duplicate_mask.sum())} rows involved."
        )

    # 11. Retrieval date validation
    retrieval_dates = pd.to_datetime(
        data["retrieved_on"],
        errors="coerce",
    )

    invalid_dates = retrieval_dates.isna()

    if invalid_dates.any():
        result.errors.append(
            f"Invalid retrieval dates: {int(invalid_dates.sum())} rows."
        )

    # 12. Coverage summary
    result.summary.update({
        "countries": int(data["iso3"].nunique()),
        "indicators": int(data["indicator"].nunique()),
        "year_min": int(years.dropna().min())
        if years.notna().any() else None,
        "year_max": int(years.dropna().max())
        if years.notna().any() else None,
        "missing_values": missing_values,
    })

    result.summary["country_codes"] = sorted(
        data["iso3"].dropna().astype(str).unique().tolist()
    )

    result.summary["indicator_names"] = sorted(
        data["indicator"].dropna().astype(str).unique().tolist()
    )

    return result


def write_report(result: ValidationResult, report_path: Path) -> None:
    """Write validation findings to a human-readable text report."""

    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "WORLD BANK DATA QUALITY REPORT",
        "=" * 40,
        "",
        f"Status: {'VALID' if result.is_valid else 'INVALID'}",
        "",
        "DATASET SUMMARY",
        "-" * 40,
    ]

    for key, value in result.summary.items():
        lines.append(f"{key}: {value}")

    lines.extend([
        "",
        f"ERRORS ({len(result.errors)})",
        "-" * 40,
    ])

    lines.extend(
        [f"- {error}" for error in result.errors]
        or ["None"]
    )

    lines.extend([
        "",
        f"WARNINGS ({len(result.warnings)})",
        "-" * 40,
    ])

    lines.extend(
        [f"- {warning}" for warning in result.warnings]
        or ["None"]
    )

    report_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate cleaned World Bank indicator data."
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/worldbank/worldbank_long.csv"),
        help="Path to cleaned long-format CSV.",
    )

    parser.add_argument(
        "--report",
        type=Path,
        default=Path("data/processed/worldbank/worldbank_quality_report.txt"),
        help="Path where the quality report will be written.",
    )

    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(
            f"Dataset not found: {args.input}"
        )

    print(f"Loading dataset: {args.input}")

    df = pd.read_csv(args.input)

    result = validate_worldbank_data(df)

    write_report(result, args.report)

    print("\nValidation completed.")
    print(f"Status: {'VALID' if result.is_valid else 'INVALID'}")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")
    print(f"Report saved to: {args.report.resolve()}")

    for error in result.errors:
        print(f"ERROR: {error}")

    for warning in result.warnings:
        print(f"WARNING: {warning}")

    if not result.is_valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
