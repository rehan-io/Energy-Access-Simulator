// frontend/src/services/api.ts
import type { Levers, YearSnapshot, CountryOption, TierKey } from '../types';

export async function fetchCountries(): Promise<CountryOption[]> {
  const res = await fetch('/api/countries');
  if (!res.ok) throw new Error('Failed to load countries');
  return res.json();
}

export async function fetchSimulation(
  levers: Levers,
  country = 'IND',
  startYear = 2026,
  years = 25,
): Promise<{ history: YearSnapshot[]; initialStocks: Record<TierKey, number> }> {
  const res = await fetch('/api/simulate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ levers, country, startYear, years }),
  });

  if (!res.ok) {
    throw new Error(`Simulation failed: ${res.statusText}`);
  }

  return res.json();
}