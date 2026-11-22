import axios from 'axios';
import type { Levers, YearSnapshot } from '../types';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

// Mirrors backend/app/main.py → SimulationRequest
export interface BackendSimRequest {
  levers: Levers;             // { subsidy, carbonTax, offGrid, gridExt }
  country: string;            // ISO3: IND, KEN, RWA, NGA
  startYear: number;
  years: number;
}

// Mirrors backend/app/main.py → simulate_endpoint return
export interface BackendSimResponse {
  country: string;
  initialStocks: Record<string, number>;
  history: YearSnapshot[];    // already row-based: [{year, traditional, ...}]
}

export async function simulateRemote(
  levers: Levers,
  country = 'IND',
  startYear = 2026,
  years = 25,
): Promise<BackendSimResponse> {
  const { data } = await api.post<BackendSimResponse>(
    '/api/simulate',
    { levers, country, startYear, years } satisfies BackendSimRequest,
  );
  return data;                // return the FULL response so we can grab initialStocks too
}

export async function pingBackend(): Promise<boolean> {
  try {
    await api.get('/api/health');
    return true;
  } catch {
    return false;
  }
}