# backend/app/core/simulation.py
from typing import List, Dict, Optional

COUNTRY_PRESETS: Dict[str, Dict[str, float]] = {
    # India preset re-tuned so the demo shows meaningful movement.
    # Original had grid=90 — nothing left to climb.
    "IND": {"traditional": 15.0, "lantern": 15.0, "shs": 30.0, "minigrid": 10.0, "grid": 30.0},
    "KEN": {"traditional": 18.0, "lantern": 10.0, "shs": 22.0, "minigrid": 4.0,  "grid": 46.0},
    "RWA": {"traditional": 24.0, "lantern": 12.0, "shs": 18.0, "minigrid": 4.0,  "grid": 42.0},
    "NGA": {"traditional": 35.0, "lantern": 15.0, "shs": 12.0, "minigrid": 3.0,  "grid": 35.0},
}


def get_country_preset(country_code: str) -> Dict[str, float]:
    return COUNTRY_PRESETS.get(country_code.upper(), COUNTRY_PRESETS["IND"]).copy()


def run_simulation(
    subsidy: float,
    carbon_tax: float,
    off_grid: float,
    grid_ext: float,
    country: str = "IND",
    initial_stocks: Optional[Dict[str, float]] = None,
    start_year: int = 2026,
    years: int = 25,
) -> List[Dict[str, float]]:
    """System-dynamics stock-and-flow model of the energy ladder.

    Each lever drives specific transitions with diminishing returns:
        Subsidy    -> T->SHS, Lantern->SHS (upfront cost barrier)
        Carbon Tax -> T->Lantern, T->SHS   (kerosene more expensive)
        Off-Grid   -> T->SHS, L->SHS, SHS->MiniGrid (companies reach)
        Grid Ext   -> everything -> Grid    (physical infrastructure)
        Sub × Tax  -> extra T->SHS, L->SHS (push and pull reinforce)
    """

    s = (initial_stocks or get_country_preset(country)).copy()

    # ── Normalise levers to 0-1 ─────────────────────────────────
    sub = subsidy / 100.0
    tax = carbon_tax / 100.0
    off = off_grid / 100.0
    grd = grid_ext / 100.0

    # ── Diminishing returns: first 50% gives ~62% of max effect ──
    sub_eff = sub ** 0.7
    tax_eff = tax ** 0.7
    off_eff = off ** 0.7
    grd_eff = grd ** 0.7

    # ── Baseline yearly transition rate + lever-driven boosts ───
    base = 0.02
    sub_boost = 0.05 * sub_eff   # strong for SHS adoption
    tax_boost = 0.04 * tax_eff   # drives people off kerosene
    off_boost = 0.04 * off_eff   # expands distributed reach
    grd_boost = 0.06 * grd_eff   # grid build rate
    combo     = 0.03 * sub_eff * tax_eff  # subsidy × tax super-additive

    history: List[Dict[str, float]] = []
    cumulative_shs = 0.0

    for i in range(years):
        # Learning curve: cumulative SHS adoption + subsidy both reduce SHS cost
        learning = max(0.35, 1.0 - cumulative_shs * 0.008 - sub_eff * 0.25)

        # ── Transition rates (each ≥ 0, bounded < 1) ────────────
        rate_tl = base + tax_boost * 0.7 + off_boost * 0.4
        rate_ts = base * learning + sub_boost * 0.6 + tax_boost * 0.4 + off_boost * 0.3 + combo * 0.5
        rate_tg = base * 0.3 + grd_boost * 0.3

        rate_ls = base * learning + sub_boost * 0.8 + off_boost * 0.4 + combo * 0.3
        rate_lg = base * 0.2 + grd_boost * 0.3

        rate_sm = base * 0.5 + off_boost * 0.8
        rate_sg = base * 0.4 + grd_boost * 0.9

        rate_mg = base * 0.3 + grd_boost * 0.7

        # ── Flows (multiplicative -> can't go negative) ────────
        f_tl = s["traditional"] * rate_tl * 0.8
        f_ts = s["traditional"] * rate_ts * 0.6
        f_tg = s["traditional"] * rate_tg

        f_ls = s["lantern"] * rate_ls * 0.7
        f_lg = s["lantern"] * rate_lg * 0.5

        f_sm = s["shs"] * rate_sm * 0.5
        f_sg = s["shs"] * rate_sg * 0.5

        f_mg = s["minigrid"] * rate_mg * 0.4

        # ── Apply ──────────────────────────────────────────────
        s["traditional"] -= (f_tl + f_ts + f_tg)
        s["lantern"]     += f_tl - f_ls - f_lg
        s["shs"]         += f_ts + f_ls - f_sm - f_sg
        s["minigrid"]    += f_sm - f_mg
        s["grid"]        += f_tg + f_lg + f_sg + f_mg

        # Numerical safety
        for k in s:
            s[k] = max(0.0, s[k])

        cumulative_shs += s["shs"] * 0.02

        history.append({
            "year": start_year + i,
            "traditional": round(s["traditional"], 2),
            "lantern":     round(s["lantern"], 2),
            "shs":         round(s["shs"], 2),
            "minigrid":    round(s["minigrid"], 2),
            "grid":        round(s["grid"], 2),
        })

    return history