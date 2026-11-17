
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class CountryBaselineInputs:
    """World Bank observations used to calibrate a country."""

    iso3: str
    year: int

    population_total: Optional[float] = None
    population_rural_pct: Optional[float] = None

    electricity_access_total_pct: Optional[float] = None
    electricity_access_rural_pct: Optional[float] = None
    electricity_access_urban_pct: Optional[float] = None

    clean_cooking_access_pct: Optional[float] = None
    gdp_per_capita_usd: Optional[float] = None

    source: str = "World Bank"

    def __post_init__(self):
        if len(self.iso3) != 3 or not self.iso3.isalpha():
            raise ValueError("iso3 must be a three-letter country code")

        if self.year < 1960:
            raise ValueError("year must be at least 1960")

        percentage_fields = (
            "population_rural_pct",
            "electricity_access_total_pct",
            "electricity_access_rural_pct",
            "electricity_access_urban_pct",
            "clean_cooking_access_pct",
        )

        for name in percentage_fields:
            value = getattr(self, name)
            if value is not None and not 0 <= value <= 100:
                raise ValueError(f"{name} must be between 0 and 100")

        for name in ("population_total", "gdp_per_capita_usd"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} cannot be negative")


@dataclass(frozen=True)
class CountryBaseline:
    """Calibrated starting state for an energy-access simulation."""

    iso3: str
    year: int

    population_total: float
    population_rural: float
    population_urban: float

    population_with_electricity: float
    population_without_electricity: float

    electricity_access_rate: float

    population_rural_with_electricity: Optional[float] = None
    population_urban_with_electricity: Optional[float] = None

    missing_indicators: tuple[str, ...] = ()
    calibration_warnings: tuple[str, ...] = ()
    source: str = "World Bank"

    def __post_init__(self):
        if self.population_total < 0:
            raise ValueError("population_total cannot be negative")

        counts = (
            self.population_rural,
            self.population_urban,
            self.population_with_electricity,
            self.population_without_electricity,
        )

        if any(value < 0 for value in counts):
            raise ValueError("population counts cannot be negative")

        if not 0 <= self.electricity_access_rate <= 1:
            raise ValueError("electricity_access_rate must be between 0 and 1")
