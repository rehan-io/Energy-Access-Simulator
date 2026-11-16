# backend/app/core/simulation.py
from typing import List, Dict, Optional

COUNTRY_PRESETS: Dict[str, Dict[str, float]] = {
    "IND": {
        "traditional": 1.0,
        "lantern": 2.0,
        "shs": 5.0,
        "minigrid": 2.0,
        "grid": 90.0,
    },
    "KEN": {
        "traditional": 18.0,
        "lantern": 10.0,
        "shs": 22.0,
        "minigrid": 4.0,
        "grid": 46.0,
    },
    "RWA": {
        "traditional": 24.0,
        "lantern": 12.0,
        "shs": 18.0,
        "minigrid": 4.0,
        "grid": 42.0,
    },
    "NGA": {
        "traditional": 35.0,
        "lantern": 15.0,
        "shs": 12.0,
        "minigrid": 3.0,
        "grid": 35.0,
    },
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
    s = (initial_stocks or get_country_preset(country)).copy()

    base_rate = 0.02
    subsidy_boost = subsidy * 0.0006
    tax_boost = carbon_tax * 0.0004
    off_grid_boost = off_grid * 0.0005
    grid_boost = grid_ext * 0.0006

    history = []
    cumulative_shs = 0.0

    for i in range(years):
        learning = max(0.4, 1.0 - cumulative_shs * 0.008)

        t_to_l = s["traditional"] * (base_rate + tax_boost) * 0.8
        t_to_s = s["traditional"] * (base_rate * learning + subsidy_boost) * 0.6
        l_to_s = s["lantern"] * (base_rate * learning + subsidy_boost) * 0.7
        s_to_m = s["shs"] * (base_rate + off_grid_boost) * 0.5
        s_to_g = s["shs"] * (base_rate + grid_boost) * 0.5
        m_to_g = s["minigrid"] * (base_rate + grid_boost) * 0.4

        s["traditional"] -= (t_to_l + t_to_s)
        s["lantern"] += (t_to_l - l_to_s)
        s["shs"] += (t_to_s + l_to_s - s_to_m - s_to_g)
        s["minigrid"] += (s_to_m - m_to_g)
        s["grid"] += (s_to_g + m_to_g)

        cumulative_shs += s["shs"] * 0.02

        history.append({
            "year": start_year + i,
            "traditional": round(s["traditional"], 2),
            "lantern": round(s["lantern"], 2),
            "shs": round(s["shs"], 2),
            "minigrid": round(s["minigrid"], 2),
            "grid": round(s["grid"], 2),
        })

    return history