
"""
World Bank dataset refresh.

Examples:
Full initial fetch:
    python -m app.data.refresh_worldbank \
        --countries IND KEN RWA NGA \
        --mode full --start 2000 --end 2026

Incremental refresh:
    python -m app.data.refresh_worldbank \
        --countries IND KEN RWA NGA \
        --mode incremental --overlap-years 3
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

from app.data.clean_worldbank import (
    clean_worldbank_data,
    normalise_data,
    remove_duplicates,
)
from app.data.validate_worldbank import (
    validate_worldbank_data,
    write_report,
)
from app.data.dataset_loader import get_data_directory
from app.data.schemas import LONG_COLUMNS, KEY_COLUMNS


def determine_incremental_start(
    existing: pd.DataFrame,
    countries: list[str],
    overlap_years: int,
    fallback_start: int,
) -> int:
    """Find the earliest year that needs refreshing."""

    country_data = existing.loc[
        existing["iso3"].isin(countries)
    ]

    if country_data.empty:
        return fallback_start

    latest_by_country = (
        country_data.groupby("iso3")["year"].max()
    )

    # If any requested country is absent, use the full fallback range.
    if not set(countries).issubset(set(latest_by_country.index)):
        return fallback_start

    earliest_latest_year = int(latest_by_country.min())

    return max(
        fallback_start,
        earliest_latest_year - overlap_years,
    )


def merge_datasets(
    existing: pd.DataFrame,
    incoming: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    """
    Merge new observations with existing observations.

    Newer retrievals replace observations with matching
    country-year-indicator keys. Unaffected observations remain.
    """

    existing = normalise_data(existing.loc[:, LONG_COLUMNS])
    incoming = normalise_data(incoming.loc[:, LONG_COLUMNS])

    existing = remove_duplicates(existing)
    incoming = remove_duplicates(incoming)

    existing_keys = set(
        map(tuple, existing.loc[:, KEY_COLUMNS].to_numpy())
    )

    incoming_keys = set(
        map(tuple, incoming.loc[:, KEY_COLUMNS].to_numpy())
    )

    added = len(incoming_keys - existing_keys)
    overlapping = len(incoming_keys & existing_keys)

    combined = pd.concat(
        [existing, incoming],
        ignore_index=True,
    )

    merged = remove_duplicates(combined)

    retained = len(existing_keys - incoming_keys)

    statistics = {
        "existing_observations": len(existing),
        "incoming_observations": len(incoming),
        "added_observations": added,
        "overlapping_observations": overlapping,
        "retained_observations": retained,
        "merged_observations": len(merged),
    }

    return merged, statistics


def promote_datasets(
    staging_dir: Path,
    active_dir: Path,
) -> None:
    """Promote validated files, restoring previous files on failure."""

    filenames = [
        "worldbank_long.csv",
        "worldbank_wide.csv",
        "worldbank_latest.csv",
        "worldbank_quality_report.txt",
    ]

    active_dir.mkdir(parents=True, exist_ok=True)

    backup_dir = staging_dir.parent / "previous_dataset"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backed_up = []
    promoted = []

    try:
        for filename in filenames:
            destination = active_dir / filename

            if destination.exists():
                shutil.copy2(
                    destination,
                    backup_dir / filename,
                )
                backed_up.append(filename)

        for filename in filenames:
            source = staging_dir / filename

            if not source.is_file():
                raise FileNotFoundError(
                    f"Staged output missing: {filename}"
                )

            source.replace(active_dir / filename)
            promoted.append(filename)

    except Exception:
        for filename in promoted:
            destination = active_dir / filename

            if destination.exists():
                destination.unlink()

        for filename in backed_up:
            shutil.copy2(
                backup_dir / filename,
                active_dir / filename,
            )

        raise

    finally:
        shutil.rmtree(backup_dir, ignore_errors=True)


def refresh_worldbank_data(
    countries: list[str],
    start: int,
    end: int,
    active_dir: Path,
    mode: str = "incremental",
    overlap_years: int = 3,
) -> None:
    """Run full or incremental refresh with validation before promotion."""

    if start > end:
        raise ValueError("Start year cannot exceed end year.")

    if overlap_years < 0:
        raise ValueError("Overlap years cannot be negative.")

    countries = list(dict.fromkeys(
        country.strip().upper()
        for country in countries
    ))

    if not countries or any(
        len(country) != 3 or not country.isalpha()
        for country in countries
    ):
        raise ValueError("Provide valid three-letter ISO3 country codes.")

    if mode not in {"full", "incremental"}:
        raise ValueError("Mode must be 'full' or 'incremental'.")

    fetch_script = Path(__file__).with_name("fetch_worldbank.py")

    if not fetch_script.is_file():
        raise FileNotFoundError(fetch_script)

    existing_file = active_dir / "worldbank_long.csv"
    existing = None

    if existing_file.is_file():
        existing = pd.read_csv(existing_file)

        missing = [
            column for column in LONG_COLUMNS
            if column not in existing.columns
        ]

        if missing:
            raise ValueError(
                f"Existing dataset is missing columns: {missing}"
            )

    if mode == "incremental" and existing is not None:
        fetch_start = determine_incremental_start(
            existing=existing,
            countries=countries,
            overlap_years=overlap_years,
            fallback_start=start,
        )
    else:
        fetch_start = start

    print(f"Refresh mode: {mode}")
    print(f"Countries: {', '.join(countries)}")
    print(f"Fetching years: {fetch_start}-{end}")

    active_dir.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="worldbank_refresh_",
        dir=active_dir.parent,
    ) as temporary_directory:

        workspace = Path(temporary_directory)
        raw_dir = workspace / "raw"
        staging_dir = workspace / "processed"

        raw_dir.mkdir()
        staging_dir.mkdir()

        # 1. Fetch
        command = [
            sys.executable,
            str(fetch_script),
            "--countries",
            *countries,
            "--start",
            str(fetch_start),
            "--end",
            str(end),
            "--outdir",
            str(raw_dir),
        ]

        subprocess.run(
            command,
            check=True,
            cwd=str(fetch_script.parents[3]),
        )

        raw_file = raw_dir / "worldbank_long.csv"

        if not raw_file.is_file():
            raise FileNotFoundError(
                "Fetcher did not produce worldbank_long.csv."
            )

        incoming = pd.read_csv(raw_file)

        # 2. Merge with existing data, or use incoming data for first setup.
        if existing is not None:
            merged, statistics = merge_datasets(
                existing,
                incoming,
            )
        else:
            merged = normalise_data(incoming)
            merged = remove_duplicates(merged)

            statistics = {
                "existing_observations": 0,
                "incoming_observations": len(incoming),
                "added_observations": len(merged),
                "overlapping_observations": 0,
                "retained_observations": 0,
                "merged_observations": len(merged),
            }

        print("\nRefresh statistics:")

        for name, value in statistics.items():
            print(f"  {name}: {value}")

        # 3. Generate all processed datasets from the merged long data.
        from app.data.clean_worldbank import (
            create_wide_dataset,
            create_latest_dataset,
        )

        wide = create_wide_dataset(merged)
        latest = create_latest_dataset(merged)

        merged.to_csv(
            staging_dir / "worldbank_long.csv",
            index=False,
        )
        wide.to_csv(
            staging_dir / "worldbank_wide.csv",
            index=False,
        )
        latest.to_csv(
            staging_dir / "worldbank_latest.csv",
            index=False,
        )

        # 4. Validate the complete merged dataset.
        result = validate_worldbank_data(merged)

        write_report(
            result,
            staging_dir / "worldbank_quality_report.txt",
        )

        print(f"\nValidation errors: {len(result.errors)}")
        print(f"Validation warnings: {len(result.warnings)}")

        if not result.is_valid:
            for error in result.errors:
                print(f"ERROR: {error}")

            raise RuntimeError(
                "Merged dataset failed validation. "
                "Active datasets have not been changed."
            )

        # 5. Promote only after successful validation.
        promote_datasets(
            staging_dir=staging_dir,
            active_dir=active_dir,
        )

    print("\nWorld Bank refresh completed successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refresh World Bank datasets."
    )

    parser.add_argument(
        "--countries",
        nargs="+",
        required=True,
    )
    parser.add_argument(
        "--mode",
        choices=["full", "incremental"],
        default="incremental",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=2000,
        help="Earliest year for full refresh or first-time setup.",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=pd.Timestamp.today().year,
    )
    parser.add_argument(
        "--overlap-years",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
    )

    args = parser.parse_args()

    active_dir = (
        args.data_dir.expanduser().resolve()
        if args.data_dir
        else get_data_directory()
    )

    refresh_worldbank_data(
        countries=args.countries,
        start=args.start,
        end=args.end,
        active_dir=active_dir,
        mode=args.mode,
        overlap_years=args.overlap_years,
    )


if __name__ == "__main__":
    main()
