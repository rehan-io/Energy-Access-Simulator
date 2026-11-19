
"""Data schemas for country-level energy access simulation baselines."""

from dataclasses import dataclass, field
from math import isfinite

from app.data.schemas import INDICATOR_CODES, PERCENTAGE_INDICATORS


@dataclass(frozen=True)
class BaselineIndicator:
    """A calibrated observation, with provenance and missing-data status."""

    name: str
    value: float | None
    observation_year: int | None
    source: str = "world_bank"

    def __post_init__(self):
        if self.name not in INDICATOR_CODES:
            raise ValueError(f"Unknown indicator: {self.name}")

        if self.value is None:
            if self.observation_year is not None:
                raise ValueError(
                    "Missing values must not have an observation year"
                )
            return

        if not isfinite(self.value) or self.value < 0:
            raise ValueError(
                f"{self.name} must be finite and non-negative"
            )

        if (
            self.name in PERCENTAGE_INDICATORS
            and self.value > 100
        ):
            raise ValueError(
                f"{self.name} must be between 0 and 100"
            )

        if (
            self.observation_year is None
            or self.observation_year < 1900
        ):
            raise ValueError("Invalid observation year")

        if not self.source.strip():
            raise ValueError("Source cannot be empty")

    @property
    def is_missing(self) -> bool:
        return self.value is None


@dataclass(frozen=True)
class CountryBaseline:
    """Validated input state for one country's simulation."""

    iso3: str
    country: str
    baseline_year: int
    indicators: dict[str, BaselineIndicator] = field(
        default_factory=dict
    )

    def __post_init__(self):
        if len(self.iso3) != 3 or not self.iso3.isalpha():
            raise ValueError("iso3 must be a three-letter code")

        if self.iso3 != self.iso3.upper():
            raise ValueError("iso3 must be uppercase")

        if not self.country.strip():
            raise ValueError("Country name cannot be empty")

        if self.baseline_year < 1900:
            raise ValueError("Invalid baseline year")

        for name, indicator in self.indicators.items():
            if name != indicator.name:
                raise ValueError(
                    f"Indicator key mismatch: {name}"
                )

            if (
                indicator.observation_year is not None
                and indicator.observation_year > self.baseline_year
            ):
                raise ValueError(
                    f"{name} cannot use a future observation"
                )

    def get_value(self, name: str) -> float | None:
        """Return an indicator value, or None if unavailable."""
        if name not in INDICATOR_CODES:
            raise ValueError(f"Unknown indicator: {name}")

        indicator = self.indicators.get(name)
        return None if indicator is None else indicator.value

    @property
    def missing_indicators(self) -> list[str]:
        return [
            name
            for name in INDICATOR_CODES
            if name not in self.indicators
            or self.indicators[name].is_missing
        ]
