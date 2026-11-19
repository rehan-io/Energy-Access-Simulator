import axios from 'axios';
import type { Levers, YearSnapshot } from '../types';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  timeout: 8000,
  headers: { 'Content-Type': 'application/json' },
});

export interface BackendSimRequest {
  country: string;
  levers: Levers;
  startYear: number;
  years: number;
}

export interface BackendSimResponse {
  country: string;
  initialStocks: Record<string, number>;
  history: YearSnapshot[];
}

export async function simulateRemote(
  levers: Levers,
  country = 'IND',
  startYear = 2026,
  years = 25,
): Promise<BackendSimResponse> {
  const { data } = await api.post<BackendSimResponse>('/api/simulate', {
    country, levers, startYear, years,
  } satisfies BackendSimRequest);
  return data;                    // ← return full response, not just data.history
}

export async function pingBackend(): Promise<boolean> {
  try { await api.get('/api/health'); return true; }
  catch { return false; }
}