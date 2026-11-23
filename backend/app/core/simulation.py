"""Coupled Bass-Logistic and Five-Tier Stock-and-Flow simulation engine."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from app.data.dataset_loader import load_wide_dataset
from app.model.calibration import get_simulation_macro_context
from app.model.calibration_schema import SimulationMacroContext


GLOBAL_OG_GROWTH = 0.13
LEARNING_RATE_GLOBAL = 0.19
BETA_GLOBAL = -math.log2(1.0 - LEARNING_RATE_GLOBAL)  # ~0.304
BETA_LOCAL = 0.10

ALPHA_GRD = 0.120
ALPHA_OFF = 0.100
ALPHA_TAX_OG = 0.030
ALPHA_GRD_U = 0.090

GAMMA_SUB_C = 0.075
GAMMA_ECOOK = 0.040
GAMMA_GRD_C = 0.025


@dataclass(frozen=True)
class CountryCalibrationParams:
    k_grid_r0: float
    k_off_r0: float
    k_u0: float
    k_cook0: float
    grid_reliability: float
    # Illustrative baseline tier splits (grid, minigrid, shs, lantern) in [0, 1]
    tier_split: tuple[float, float, float, float]


COUNTRY_CALIBRATION_PARAMS: dict[str, CountryCalibrationParams] = {
    "IND": CountryCalibrationParams(
        k_grid_r0=0.090,
        k_off_r0=0.020,
        k_u0=0.200,
        k_cook0=0.095,
        grid_reliability=0.95,
        tier_split=(0.96, 0.01, 0.02, 0.009),
    ),
    "KEN": CountryCalibrationParams(
        k_grid_r0=0.055,
        k_off_r0=0.040,
        k_u0=0.180,
        k_cook0=0.075,
        grid_reliability=0.75,
        tier_split=(0.52, 0.03, 0.14, 0.08),
    ),
    "RWA": CountryCalibrationParams(
        k_grid_r0=0.080,
        k_off_r0=0.045,
        k_u0=0.160,
        k_cook0=0.065,
        grid_reliability=0.75,
        tier_split=(0.48, 0.03, 0.14, 0.07),
    ),
    "NGA": CountryCalibrationParams(
        k_grid_r0=0.012,
        k_off_r0=0.015,
        k_u0=0.030,
        k_cook0=0.080,
        grid_reliability=0.45,
        tier_split=(0.54, 0.02, 0.045, 0.02),
    ),
}

DEFAULT_CALIBRATION_PARAMS = CountryCalibrationParams(
    k_grid_r0=0.055,
    k_off_r0=0.030,
    k_u0=0.150,
    k_cook0=0.075,
    grid_reliability=0.70,
    tier_split=(0.50, 0.02, 0.10, 0.05),
)


def get_country_params(country_code: str) -> CountryCalibrationParams:
    return COUNTRY_CALIBRATION_PARAMS.get(
        country_code.strip().upper(),
        DEFAULT_CALIBRATION_PARAMS,
    )


def compute_initial_tier_stocks(
    country_code: str,
    elec_access_total_pct: float,
) -> dict[str, float]:
    """Scale illustrative 2024 tier splits so electrified tiers sum to E_total."""

    e_total = min(1.0, max(0.0, elec_access_total_pct / 100.0))
    params = get_country_params(country_code)
    s_e0, s_d0, s_c0, s_b0 = params.tier_split
    split_sum = s_e0 + s_d0 + s_c0 + s_b0

    if split_sum <= 0:
        s_e = e_total
        s_d = 0.0
        s_c = 0.0
        s_b = 0.0
    else:
        scale = e_total / split_sum
        s_e = s_e0 * scale
        s_d = s_d0 * scale
        s_c = s_c0 * scale
        s_b = s_b0 * scale

    s_a = max(0.0, 1.0 - (s_b + s_c + s_d + s_e))
    return {
        "traditional": s_a,
        "lantern": s_b,
        "shs": s_c,
        "minigrid": s_d,
        "grid": s_e,
    }


def run_coupled_simulation(
    *,
    country: str,
    baseline_year: int,
    years: int,
    elec_total_pct: float,
    elec_rural_pct: float,
    elec_urban_pct: float,
    clean_cooking_pct: float,
    macro: SimulationMacroContext,
    subsidy: float = 0.0,
    carbon_tax: float = 0.0,
    off_grid: float = 0.0,
    grid_ext: float = 0.0,
    recycle_tax_revenue: bool = True,
    initial_stocks: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Run the Coupled Bass-Logistic and Five-Tier Stock-and-Flow difference model."""

    for name, val in (
        ("subsidy", subsidy),
        ("carbon_tax", carbon_tax),
        ("off_grid", off_grid),
        ("grid_ext", grid_ext),
    ):
        if not math.isfinite(val) or not 0.0 <= val <= 100.0:
            raise ValueError(f"{name} must be a finite percentage in [0, 100]")

    if years < 1 or years > 100:
        raise ValueError("years must be between 1 and 100")

    params = get_country_params(country)

    # 1. Normalized policy levers with empirical diminishing marginal returns
    s_sub = (subsidy / 100.0) ** 0.65
    s_tax = (carbon_tax / 100.0) ** 0.70
    s_off = (off_grid / 100.0) ** 0.75
    s_grd = (grid_ext / 100.0) ** 0.80

    # State variables in [0, 1]
    e_r = min(1.0, max(0.0, elec_rural_pct / 100.0))
    e_u = min(1.0, max(0.0, elec_urban_pct / 100.0))
    c_t = min(1.0, max(0.0, clean_cooking_pct / 100.0))
    r_t = min(0.95, max(0.05, macro.rural_pop_share))
    gdp_pc = max(100.0, macro.gdp_per_capita_usd)
    b80 = max(0.5, min(1.5, macro.bottom_80_income_share / 60.0))

    if initial_stocks is not None:
        # Accept either fractions summing to ~1 or percentages summing to ~100
        raw_sum = sum(initial_stocks.values())
        divisor = 100.0 if raw_sum > 1.5 else 1.0
        s_a = max(0.0, initial_stocks.get("traditional", 0.0) / divisor)
        s_b = max(0.0, initial_stocks.get("lantern", 0.0) / divisor)
        s_c = max(0.0, initial_stocks.get("shs", 0.0) / divisor)
        s_d = max(0.0, initial_stocks.get("minigrid", 0.0) / divisor)
        s_e = max(0.0, initial_stocks.get("grid", 0.0) / divisor)
        total_s = s_a + s_b + s_c + s_d + s_e
        if total_s > 0:
            s_a, s_b, s_c, s_d, s_e = (
                s_a / total_s,
                s_b / total_s,
                s_c / total_s,
                s_d / total_s,
                s_e / total_s,
            )
    else:
        stocks = compute_initial_tier_stocks(country, elec_total_pct)
        s_a = stocks["traditional"]
        s_b = stocks["lantern"]
        s_c = stocks["shs"]
        s_d = stocks["minigrid"]
        s_e = stocks["grid"]

    baseline_stocks_pct = {
        "traditional": round(s_a * 100.0, 4),
        "lantern": round(s_b * 100.0, 4),
        "shs": round(s_c * 100.0, 4),
        "minigrid": round(s_d * 100.0, 4),
        "grid": round(s_e * 100.0, 4),
    }

    q_global = 1.0
    q_local = 1.0
    initial_og_share = max(0.05, s_b + s_c + s_d)

    projected_rows: list[dict[str, Any]] = []

    for step in range(1, years + 1):
        # 2. Wright's Law cost index & price-elastic off-grid multiplier
        c_og = (q_global ** (-BETA_GLOBAL)) * (q_local ** (-BETA_LOCAL))
        p_og_eff = max(0.15, c_og * (1.0 - 0.80 * s_sub))
        p_inv = p_og_eff ** (-1.6)
        phi_og = p_inv / (1.0 + 0.25 * (p_inv - 1.0))

        # 3. Income modifier
        y_t = min(1.35, max(0.75, (gdp_pc / 1500.0) ** 0.25))

        # 4. Rural & Urban electrification hazards
        l_r = 1.0 / (1.0 + 1.8 * (e_r ** 3))
        h_grid_r = (
            (params.k_grid_r0 * y_t + ALPHA_GRD * s_grd)
            * (1.0 + 0.45 * s_sub)
            * l_r
            + 0.025 * s_sub * y_t
        )
        h_off_r = (
            (
                params.k_off_r0 * b80
                + ALPHA_OFF * s_off * phi_og
                + 0.030 * (phi_og - 1.0)
            )
            * (1.0 - 0.35 * s_grd * l_r)
            + ALPHA_TAX_OG * s_tax * (0.45 + 0.55 * s_sub)
        )
        b_r = 0.06 + 0.94 * e_r
        delta_e_r = (1.0 - e_r) * (1.0 - math.exp(-b_r * (h_grid_r + h_off_r)))

        h_u = (
            params.k_u0 * y_t
            + ALPHA_GRD_U * s_grd * (1.0 + 0.40 * s_sub)
            + 0.030 * s_sub
            + 0.020 * s_off * (1.0 - e_u)
        )
        delta_e_u = (1.0 - e_u) * (1.0 - math.exp(-(0.15 + 0.85 * e_u) * h_u))

        e_r_next = min(1.0, max(0.0, e_r + delta_e_r))
        e_u_next = min(1.0, max(0.0, e_u + delta_e_u))
        r_next = min(0.95, max(0.05, r_t + macro.rural_pop_drift))
        e_total_next = min(
            1.0,
            max(0.0, r_next * e_r_next + (1.0 - r_next) * e_u_next),
        )

        # 6. Clean cooking with carbon-tax shielding, stacking, & Tier 3+ eCooking
        e_tier3_plus = params.grid_reliability * s_e + 0.60 * s_d
        rho_shield = 1.0 if recycle_tax_revenue else min(1.0, 1.25 * s_sub)
        d_tax = (
            0.045
            * s_tax
            * (1.0 - rho_shield)
            * (1.0 - 0.50 * min(1.0, y_t))
        )
        p_tax = 0.035 * s_tax * (rho_shield + 0.50 * e_tier3_plus)
        f_stack = 1.0 / (1.0 + 0.80 * (c_t ** 2) * (1.0 - 0.60 * s_sub))
        h_cook = max(
            0.005,
            params.k_cook0 * y_t * b80
            + GAMMA_SUB_C * s_sub * b80
            + GAMMA_ECOOK * e_tier3_plus * (0.35 + 0.65 * s_sub)
            + GAMMA_GRD_C * s_grd * (0.30 + 0.70 * s_sub)
            + p_tax
            - d_tax,
        )
        delta_c = (1.0 - c_t) * (
            1.0 - math.exp(-(0.08 + 0.92 * c_t) * h_cook * f_stack)
        )
        c_next = min(1.0, max(0.0, c_t + delta_c))

        # 5. Synchronized five-tier ladder stocks
        electrified_curr = s_b + s_c + s_d + s_e
        net_new = e_total_next - electrified_curr

        raw_w_e = max(1e-6, r_t * h_grid_r + (1.0 - r_t) * h_u)
        raw_w_d = 0.25 * s_off + 0.05
        raw_w_c = (
            0.50 * (s_off + 0.50 * s_sub + 0.35 * (phi_og - 1.0)) + 0.08
        )
        raw_w_b = 0.25 * s_tax + 0.05
        w_sum = raw_w_b + raw_w_c + raw_w_d + raw_w_e
        w_b = raw_w_b / w_sum
        w_c = raw_w_c / w_sum
        w_d = raw_w_d / w_sum
        w_e = raw_w_e / w_sum

        # Upward ladder transitions among existing electrified stocks
        p_bc = 1.0 - math.exp(
            -(0.02 + 0.06 * s_sub + 0.025 * (phi_og - 1.0) + 0.03 * s_off)
        )
        p_cd = 1.0 - math.exp(-(0.01 + 0.04 * s_off))
        p_be = 1.0 - math.exp(
            -(0.01 + 0.05 * s_grd * (1.0 + 0.35 * s_sub))
        )
        p_ce = 1.0 - math.exp(
            -(0.015 + 0.06 * s_grd * (1.0 + 0.35 * s_sub))
        )
        p_de = 1.0 - math.exp(
            -(0.01 + 0.045 * s_grd * (1.0 + 0.35 * s_sub))
        )

        f_bc = s_b * p_bc
        f_be = (s_b - f_bc) * p_be
        f_cd = s_c * p_cd
        f_ce = (s_c - f_cd) * p_ce
        f_de = s_d * p_de

        s_b_up = s_b - f_bc - f_be
        s_c_up = s_c + f_bc - f_cd - f_ce
        s_d_up = s_d + f_cd - f_de
        s_e_up = s_e + f_be + f_ce + f_de

        if net_new >= 0.0:
            add_b = net_new * w_b
            add_c = net_new * w_c
            add_d = net_new * w_d
            add_e = net_new * w_e
            s_b_next = s_b_up + add_b
            s_c_next = s_c_up + add_c
            s_d_next = s_d_up + add_d
            s_e_next = s_e_up + add_e
        else:
            add_b = add_c = add_d = 0.0
            scale_down = (
                e_total_next / electrified_curr
                if electrified_curr > 0
                else 0.0
            )
            s_b_next = s_b_up * scale_down
            s_c_next = s_c_up * scale_down
            s_d_next = s_d_up * scale_down
            s_e_next = s_e_up * scale_down

        s_a_next = max(0.0, 1.0 - (s_b_next + s_c_next + s_d_next + s_e_next))

        # Advance state and learning stocks
        og_new_flow = add_b + add_c + add_d + f_bc + f_cd
        q_global *= 1.0 + GLOBAL_OG_GROWTH
        q_local += (og_new_flow / initial_og_share) + 0.05 * s_off
        gdp_pc *= 1.0 + macro.gdp_growth_rate

        e_r, e_u, c_t, r_t = e_r_next, e_u_next, c_next, r_next
        s_a, s_b, s_c, s_d, s_e = (
            s_a_next,
            s_b_next,
            s_c_next,
            s_d_next,
            s_e_next,
        )

        projected_rows.append({
            "year": baseline_year + step,
            "kind": "projected",
            "elec_access_total": round(e_total_next * 100.0, 4),
            "elec_access_rural": round(e_r_next * 100.0, 4),
            "elec_access_urban": round(e_u_next * 100.0, 4),
            "clean_cooking_access": round(c_next * 100.0, 4),
            "traditional": round(s_a_next * 100.0, 4),
            "lantern": round(s_b_next * 100.0, 4),
            "shs": round(s_c_next * 100.0, 4),
            "minigrid": round(s_d_next * 100.0, 4),
            "grid": round(s_e_next * 100.0, 4),
        })

    return {
        "baselineStocks": baseline_stocks_pct,
        "projected": projected_rows,
    }


def run_simulation(
    subsidy: float,
    carbon_tax: float,
    off_grid: float,
    grid_ext: float,
    country: str = "IND",
    initial_stocks: dict[str, float] | None = None,
    start_year: int | None = None,
    years: int = 25,
    recycle_tax_revenue: bool = True,
    data_dir=None,
) -> list[dict[str, Any]]:
    """Run the calibrated five-tier + access simulation directly from World Bank baselines."""

    iso3 = country.strip().upper()
    macro = get_simulation_macro_context(iso3, data_dir=data_dir)
    baseline_year = macro.baseline_year

    elec_total = 75.0
    elec_rural = 65.0
    elec_urban = 95.0
    clean_cooking = 40.0

    try:
        wide = load_wide_dataset(data_dir)
        row_df = wide[
            (wide["iso3"].astype(str).str.upper() == iso3)
            & (wide["year"] == baseline_year)
        ]
        if not row_df.empty:
            row = row_df.iloc[-1]
            if row.get("elec_access_total") == row.get("elec_access_total"):
                elec_total = float(row["elec_access_total"])
            if row.get("elec_access_rural") == row.get("elec_access_rural"):
                elec_rural = float(row["elec_access_rural"])
            if row.get("elec_access_urban") == row.get("elec_access_urban"):
                elec_urban = float(row["elec_access_urban"])
            if row.get("clean_cooking_access") == row.get("clean_cooking_access"):
                clean_cooking = float(row["clean_cooking_access"])
    except (FileNotFoundError, ValueError, RuntimeError):
        pass

    effective_base_year = (start_year - 1) if start_year is not None else baseline_year

    result = run_coupled_simulation(
        country=iso3,
        baseline_year=effective_base_year,
        years=years,
        elec_total_pct=elec_total,
        elec_rural_pct=elec_rural,
        elec_urban_pct=elec_urban,
        clean_cooking_pct=clean_cooking,
        macro=macro,
        subsidy=subsidy,
        carbon_tax=carbon_tax,
        off_grid=off_grid,
        grid_ext=grid_ext,
        recycle_tax_revenue=recycle_tax_revenue,
        initial_stocks=initial_stocks,
    )
    return result["projected"]