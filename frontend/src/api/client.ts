// frontend/src/api/client.ts
import axios from 'axios';
import type { Levers, YearSnapshot } from '../types';
import { stocksFromAccessAndLevers } from '../utils/calibration';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

export interface BackendSimRequest {
  country: string;
  years: number;
  trendWindow: number;
  policyAdjustments: Record<string, number>;
}

export type AccessRow =
  | {
      year: number;
      kind: 'historical';
      elec_access_total: number | null;
      elec_access_rural: number | null;
      elec_access_urban: number | null;
      clean_cooking_access: number | null;
    }
  | {
      year: number;
      kind: 'projected';
      elec_access_total: number;
      elec_access_rural: number;
      elec_access_urban: number;
      clean_cooking_access: number;
    };

export interface BackendSimResponse {
  baselineYear: number;
  trendWindow: number;
  trends: Record<string, { annual_trend: number; latest_value: number; latest_year: number }>;
  policyAdjustments: Record<string, number>;
  history: AccessRow[];
}

/**
 * Lever → backend policy adjustment (percentage points / year).
 * Coefficients amplified ~4x from the original so the access trend
 * itself moves visibly, and the SHARE ROTATION in the calibration
 * does the rest of the visual work.
 */
export function leversToAdjustments(levers: Levers): Record<string, number> {
  const sub = levers.subsidy   / 100;
  const tax = levers.carbonTax / 100;
  const off = levers.offGrid   / 100;
  const grd = levers.gridExt   / 100;

  return {
    // Every lever contributes to total access
    elec_access_total:    +(0.50 * sub + 0.70 * grd + 0.60 * tax + 0.40 * off).toFixed(4),
    elec_access_rural:    +(0.40 * off + 0.30 * sub).toFixed(4),
    elec_access_urban:    +(0.30 * grd).toFixed(4),
    clean_cooking_access: +(0.60 * tax + 0.20 * sub).toFixed(4),
  };
}

function accessHistoryToStocks(
  history: AccessRow[],
  levers: Levers,
  startYear = 2026,
  years = 25,
): YearSnapshot[] {
  const projected = history.filter(
    (r): r is Extract<AccessRow, { kind: 'projected' }> => r.kind === 'projected',
  );

  const result: YearSnapshot[] = [];

  for (let i = 0; i < years; i++) {
    const targetYear = startYear + i;

    let best: (typeof projected)[number] | null = null;
    let bestDist = Infinity;
    for (const r of projected) {
      const d = Math.abs(r.year - targetYear);
      if (d < bestDist) { bestDist = d; best = r; }
    }
    if (!best) continue;

    const s = stocksFromAccessAndLevers(best.elec_access_total, levers);
    result.push({
      year: targetYear,
      traditional: s.traditional,
      lantern:     s.lantern,
      shs:         s.shs,
      minigrid:    s.minigrid,
      grid:        s.grid,
    });
  }

  return result;
}

export async function simulateRemote(
  levers: Levers,
  country = 'IND',
  startYear = 2026,
  years = 25,
): Promise<{ initialStocks: Record<string, number>; history: YearSnapshot[] }> {
  const requestYears = years + 10;

  const payload: BackendSimRequest = {
    country,
    years: requestYears,
    trendWindow: 10,
    policyAdjustments: leversToAdjustments(levers),
  };

  const { data } = await api.post<BackendSimResponse>('/api/simulate', payload);

  const baseline = data.history.find(
    (r) => r.year === data.baselineYear && r.kind === 'historical',
  );
  const baselineAccess =
    baseline && 'elec_access_total' in baseline ? baseline.elec_access_total : null;

  const initialStocks = stocksFromAccessAndLevers(baselineAccess, levers);

  return {
    initialStocks,
    history: accessHistoryToStocks(data.history, levers, startYear, years),
  };
}

export async function pingBackend(): Promise<boolean> {
  try { await api.get('/api/health'); return true; }
  catch { return false; }
}