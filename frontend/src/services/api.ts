// frontend/src/services/api.ts
import type { Levers, YearSnapshot } from '../types';

export async function fetchSimulation(levers: Levers, startYear = 2026, years = 25): Promise<YearSnapshot[]> {
  const res = await fetch('/api/simulate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ levers, startYear, years }),
  });

  if (!res.ok) {
    throw new Error(`Simulation failed: ${res.statusText}`);
  }

  const data = await res.json();
  return data.history;
}