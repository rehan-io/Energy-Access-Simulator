
"""
Execute a safe World Bank dataset refresh.

    1. Fetch raw observations into a temporary directory.
    2. Clean and transform the raw observations.
    3. Validate the cleaned long-format dataset.
    4. Promote the processed files only if validation succeeds.

Run from the backend directory:

    python -m app.data.refresh_worldbank --countries IND KEN RWA NGA  etc

"""

import argparse
import shutil
import subprocess
import sys
import tempfile

from pathlib import Path

import pandas as pd

from app.data.clean_worldbank import clean_worldbank_data
from app.data.validate_worldbank import (
    validate_worldbank_data,
    write_report,
)
from app.data.dataset_loader import get_data_directory


def promote_datasets(
    staging_dir: Path,
    active_dir: Path,
) -> None:
    """
    Replace active datasets with validated staged datasets.

    Existing files are backed up first. If promotion fails,
    the previous files are restored.
    """

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
        # Back up existing files.
        for filename in filenames:
            active_file = active_dir / filename

            if active_file.exists():
                shutil.copy2(
                    active_file,
                    backup_dir / filename,
                )
                backed_up.append(filename)

        # Promote the validated files.
        for filename in filenames:
            source = staging_dir / filename

            if not source.is_file():
                raise FileNotFoundError(
                    f"Staged output is missing: {filename}"
                )

            destination = active_dir / filename

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            source.replace(destination)
            promoted.append(filename)

    except Exception:
        # Remove files that were already promoted.
        for filename in promoted:
            destination = active_dir / filename

            if destination.exists():
                destination.unlink()

        # Restore the previous versions.
        for filename in backed_up:
            shutil.copy2(
                backup_dir / filename,
                active_dir / filename,
            )

        raise

    finally:
        shutil.rmtree(
            backup_dir,
            ignore_errors=True,
        )


def refresh_worldbank_data(
    countries: list[str],
    start: int,
    end: int,
    active_dir: Path,
) -> None:
    """Execute the complete staged refresh workflow."""

    if start > end:
        raise ValueError("Start year cannot exceed end year.")

    countries = [
        country.strip().upper()
        for country in countries
    ]

    if not countries or any(
        len(country) != 3 or not country.isalpha()
        for country in countries
    ):
        raise ValueError(
            "Provide valid three-letter ISO3 country codes."
        )

    countries = list(dict.fromkeys(countries))

    fetch_script = Path(__file__).with_name(
        "fetch_worldbank.py"
    )

    if not fetch_script.is_file():
        raise FileNotFoundError(
            f"World Bank fetcher not found: {fetch_script}"
        )

    print("Starting World Bank dataset refresh...")
    print(f"Countries: {', '.join(countries)}")
    print(f"Years: {start}-{end}")
    print(f"Active dataset directory: {active_dir}")

    # Temporary workspace is created beside the active dataset directory.
    active_dir.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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
        print("\n[1/4] Fetching World Bank observations...")

        command = [
            sys.executable,
            str(fetch_script),
            "--countries",
            *countries,
            "--start",
            str(start),
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

        # 2. Clean
        print("\n[2/4] Cleaning and transforming observations...")

        clean_worldbank_data(
            input_path=raw_file,
            output_dir=staging_dir,
        )

        # 3. Validate
        print("\n[3/4] Validating processed observations...")

        cleaned_file = staging_dir / "worldbank_long.csv"

        cleaned_df = pd.read_csv(cleaned_file)

        result = validate_worldbank_data(cleaned_df)

        report_file = staging_dir / "worldbank_quality_report.txt"

        write_report(result, report_file)

        print(f"Validation errors: {len(result.errors)}")
        print(f"Validation warnings: {len(result.warnings)}")

        if not result.is_valid:
            for error in result.errors:
                print(f"ERROR: {error}")

            raise RuntimeError(
                "Dataset validation failed. "
                "The existing active dataset has not been changed."
            )

        # 4. Promote
        print("\n[4/4] Promoting validated datasets...")

        promote_datasets(
            staging_dir=staging_dir,
            active_dir=active_dir,
        )

    print("\nWorld Bank dataset refresh completed successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Safely refresh processed World Bank datasets."
    )

    parser.add_argument(
        "--countries",
        nargs="+",
        required=True,
        help="ISO3 country codes, e.g. IND KEN RWA NGA.",
    )

    parser.add_argument(
        "--start",
        type=int,
        default=2000,
        help="Starting observation year.",
    )

    parser.add_argument(
        "--end",
        type=int,
        default=2025,
        help="Ending observation year.",
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Destination for active processed datasets.",
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
    )


if __name__ == "__main__":
    main()
