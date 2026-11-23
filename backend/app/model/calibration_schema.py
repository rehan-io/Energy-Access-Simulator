"""Schemas for converting World Bank observations into model baselines."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CountryBaselineInputs:
    """World Bank observations used to calibrate a country."""

    iso3: str
    year: int

    population_total: float | None = None
    population_rural_pct: float | None = None

    electricity_access_total_pct: float | None = None
    electricity_access_rural_pct: float | None = None
    electricity_access_urban_pct: float | None = None

    clean_cooking_access_pct: float | None = None
    elec_use_kwh_pc: float | None = None
    gdp_per_capita_usd: float | None = None

    income_share_q1: float | None = None
    income_share_q2: float | None = None
    income_share_q3: float | None = None
    income_share_q4: float | None = None
    income_share_q5: float | None = None

    observation_years: dict[str, int] = field(default_factory=dict)
    source: str = "World Bank"

    def __post_init__(self):
        if len(self.iso3) != 3 or not self.iso3.isalpha():
            raise ValueError("iso3 must be a three-letter country code")

        if self.iso3 != self.iso3.upper():
            raise ValueError("iso3 must be uppercase")

        if self.year < 1900:
            raise ValueError("Invalid baseline year")

        percentage_fields = (
            "population_rural_pct",
            "electricity_access_total_pct",
            "electricity_access_rural_pct",
            "electricity_access_urban_pct",
            "clean_cooking_access_pct",
            "income_share_q1",
            "income_share_q2",
            "income_share_q3",
            "income_share_q4",
            "income_share_q5",
        )

        for name in percentage_fields:
            value = getattr(self, name)
            if value is not None and not 0 <= value <= 100:
                raise ValueError(f"{name} must be between 0 and 100")

        for name in ("population_total", "gdp_per_capita_usd", "elec_use_kwh_pc"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} cannot be negative")


@dataclass(frozen=True)
class CalibratedCountryBaseline:
    """Derived country population and electricity-access baseline."""

    iso3: str
    year: int

    population_total: float
    population_rural: float
    population_urban: float

    population_with_electricity: float
    population_without_electricity: float

    electricity_access_rate: float

    population_rural_with_electricity: float | None = None
    population_urban_with_electricity: float | None = None

    population_rural_without_electricity: float | None = None
    population_urban_without_electricity: float | None = None

    electricity_access_rural_pct: float | None = None
    electricity_access_urban_pct: float | None = None
    clean_cooking_access_pct: float | None = None
    elec_use_kwh_pc: float | None = None
    gdp_per_capita_usd: float | None = None
    bottom_80_income_share_pct: float | None = None

    observation_years: dict[str, int] = field(default_factory=dict)
    missing_indicators: tuple[str, ...] = ()
    calibration_warnings: tuple[str, ...] = ()
    source: str = "World Bank"

    def __post_init__(self):
        if self.population_total <= 0:
            raise ValueError("population_total must be positive")

        counts = (
            self.population_rural,
            self.population_urban,
            self.population_with_electricity,
            self.population_without_electricity,
        )

        if any(value < 0 for value in counts):
            raise ValueError("Population counts cannot be negative")

        if abs(
            self.population_rural + self.population_urban
            - self.population_total
        ) > max(1.0, self.population_total * 1e-8):
            raise ValueError("Rural and urban population must sum to total")

        if abs(
            self.population_with_electricity
            + self.population_without_electricity
            - self.population_total
        ) > max(1.0, self.population_total * 1e-8):
            raise ValueError("Electrified and unelectrified population must sum to total")

        if not 0 <= self.electricity_access_rate <= 1:
            raise ValueError("electricity_access_rate must be between 0 and 1")


@dataclass(frozen=True)
class SimulationMacroContext:
    """Macroeconomic and demographic context extracted from worldbank_wide.csv."""

    iso3: str
    baseline_year: int
    rural_pop_share: float        # fraction in [0.05, 0.95]
    rural_pop_drift: float        # annual change in fraction (e.g. -0.0031)
    gdp_per_capita_usd: float     # baseline-year GDP per capita
    gdp_growth_rate: float        # clamped annual growth rate
    bottom_80_income_share: float # percentage in (0, 100]
    elec_use_kwh_pc: float | None = None