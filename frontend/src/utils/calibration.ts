// frontend/src/utils/calibration.ts
import type { Levers } from '../types';

/**
 * Derive the 5 stock values from an access rate + lever settings.
 *
 * Two effects compose:
 *   1. Access rate sets the CONNECTED fraction (grid + shs + minigrid + lantern)
 *   2. Levers ROTATE shares between the four connected tiers
 *
 * This is intentionally stronger than the pure-access calibration so
 * every lever visibly moves the chart.
 */
export function stocksFromAccessAndLevers(
  access: number | null,
  levers: Levers,
): Record<string, number> {
  const a = Math.max(0, Math.min(100, access ?? 50));
  const factor = Math.max(0, Math.min(1, (a - 50) / 50));

  const connected = a;
  const traditional = 100 - connected;

  // Base shares among CONNECTED population — capped at 0.72 so there's
  // headroom for grid to grow AND shrink with levers.
  const grid_share    = 0.55 + 0.17 * factor;  // 0.55 → 0.72
  const shs_share     = 0.28 - 0.10 * factor;  // 0.28 → 0.18
  const mini_share    = 0.12 - 0.04 * factor;  // 0.12 → 0.08
  const lantern_share = Math.max(0.01, 1 - grid_share - shs_share - mini_share);

  const sub = levers.subsidy   / 100;
  const off = levers.offGrid   / 100;
  const grd = levers.gridExt   / 100;

  // Rotation multipliers. Coefficients chosen so every multiplier stays
  // strictly positive across the full lever space (0..100 each).
  const grid_pref    = grid_share    * (1 + 0.9 * grd - 0.5 * off - 0.3 * sub);
  const shs_pref     = shs_share     * (1 + 0.8 * sub + 0.6 * off - 0.4 * grd);
  const mini_pref    = mini_share    * (1 + 0.6 * off - 0.3 * grd);
  const lantern_pref = lantern_share * (1 + 0.3 * sub - 0.4 * off);

  const sum = grid_pref + shs_pref + mini_pref + lantern_pref;
  const scale = sum > 0 ? 1 / sum : 1;

  const stocks = {
    traditional: +traditional.toFixed(2),
    lantern:     +(connected * lantern_pref * scale).toFixed(2),
    shs:         +(connected * shs_pref     * scale).toFixed(2),
    minigrid:    +(connected * mini_pref    * scale).toFixed(2),
    grid:        +(connected * grid_pref    * scale).toFixed(2),
  };

  // Absorb rounding drift into grid so the 5 stocks sum to exactly 100
  const total = Object.values(stocks).reduce((x, y) => x + y, 0);
  if (Math.abs(total - 100) > 0.01 && total > 0) {
    stocks.grid = +(stocks.grid + (100 - total)).toFixed(2);
  }

  return stocks;
}