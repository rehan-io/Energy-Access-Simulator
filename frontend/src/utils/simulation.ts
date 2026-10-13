import type { Levers, YearSnapshot } from '../types';

export function simulate(
  levers: Levers,
  startYear = 2026,
  years = 25,
): YearSnapshot[] {
  let s = { traditional: 60, lantern: 20, shs: 12, minigrid: 4, grid: 4 };

  const baseRate = 0.02;
  const subsidyBoost  = levers.subsidy   * 0.0006;
  const taxBoost      = levers.carbonTax * 0.0004;
  const offGridBoost  = levers.offGrid   * 0.0005;
  const gridBoost     = levers.gridExt   * 0.0006;

  const history: YearSnapshot[] = [];
  let cumulativeSHS = 0;

  for (let i = 0; i < years; i++) {
    // Learning curve: SHS cost drops with cumulative adoption
    const learning = Math.max(0.4, 1 - cumulativeSHS * 0.008);

    const t_to_l = s.traditional * (baseRate + taxBoost) * 0.8;
    const t_to_s = s.traditional * (baseRate * learning + subsidyBoost) * 0.6;
    const l_to_s = s.lantern     * (baseRate * learning + subsidyBoost) * 0.7;
    const s_to_m = s.shs         * (baseRate + offGridBoost) * 0.5;
    const s_to_g = s.shs         * (baseRate + gridBoost)    * 0.5;
    const m_to_g = s.minigrid    * (baseRate + gridBoost)    * 0.4;

    s.traditional -= t_to_l + t_to_s;
    s.lantern     += t_to_l - l_to_s;
    s.shs         += t_to_s + l_to_s - s_to_m - s_to_g;
    s.minigrid    += s_to_m - m_to_g;
    s.grid        += s_to_g + m_to_g;

    cumulativeSHS += s.shs * 0.02;

    history.push({
      year: startYear + i,
      traditional: +s.traditional.toFixed(2),
      lantern:     +s.lantern.toFixed(2),
      shs:         +s.shs.toFixed(2),
      minigrid:    +s.minigrid.toFixed(2),
      grid:        +s.grid.toFixed(2),
    });
  }

  return history;
}