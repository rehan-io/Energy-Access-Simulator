
"""
Utilities for loading processed World Bank datasets.

The data directory can be configured through WORLD_BANK_DATA_DIR.

Default:
    backend/data/processed/worldbank/

Expected files:
    worldbank_long.csv
    worldbank_wide.csv
    worldbank_latest.csv
"""

import os
from pathlib import Path

import pandas as pd

from app.data.schemas import LONG_COLUMNS


DATASET_FILES = {
    "long": "worldbank_long.csv",
    "wide": "worldbank_wide.csv",
    "latest": "worldbank_latest.csv",
}

WIDE_REQUIRED_COLUMNS = (
    "country",
    "iso3",
    "year",
)


def get_data_directory() -> Path:
    """Resolve the processed dataset directory."""

    configured_path = os.getenv("WORLD_BANK_DATA_DIR")

    if configured_path:
        return Path(configured_path).expanduser().resolve()

    # Default location inside the backend directory.
    backend_dir = Path(__file__).resolve().parents[2]

    return (
        backend_dir
        / "data"
        / "processed"
        / "worldbank"
    )


def load_dataset(
    dataset_type: str = "long",
    data_dir: Path | str | None = None,
) -> pd.DataFrame:
    """
    Load a processed World Bank dataset.

    Args:
        dataset_type: One of 'long', 'wide', or 'latest'.
        data_dir: Optional override for the processed data directory.

    Returns:
        A pandas DataFrame containing the requested dataset.

    Raises:
        ValueError: If an unsupported dataset type is requested.
        FileNotFoundError: If the requested CSV does not exist.
        RuntimeError: If the CSV cannot be read.
        ValueError: If required columns are missing.
    """

    if dataset_type not in DATASET_FILES:
        supported = ", ".join(DATASET_FILES)
        raise ValueError(
            f"Unsupported dataset type '{dataset_type}'. "
            f"Choose from: {supported}."
        )

    directory = (
        Path(data_dir).expanduser().resolve()
        if data_dir is not None
        else get_data_directory()
    )

    file_path = directory / DATASET_FILES[dataset_type]

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Processed dataset not found: {file_path}. "
            "Run the data ingestion and cleaning pipeline first."
        )

    try:
        df = pd.read_csv(file_path)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise RuntimeError(
            f"Could not read processed dataset: {file_path}"
        ) from exc

    if dataset_type in ("long", "latest"):
        required_columns = LONG_COLUMNS
    else:
        required_columns = WIDE_REQUIRED_COLUMNS

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Dataset '{file_path.name}' is missing required "
            f"columns: {missing_columns}"
        )

    return df


def load_long_dataset(
    data_dir: Path | str | None = None,
) -> pd.DataFrame:
    """Load long-format country-year-indicator observations."""

    return load_dataset("long", data_dir)


def load_wide_dataset(
    data_dir: Path | str | None = None,
) -> pd.DataFrame:
    """Load wide-format country-year observations."""

    return load_dataset("wide", data_dir)


def load_latest_dataset(
    data_dir: Path | str | None = None,
) -> pd.DataFrame:
    """Load the latest available observation per country and indicator."""

    return load_dataset("latest", data_dir)
