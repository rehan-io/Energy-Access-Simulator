import { create } from 'zustand';
import type { Levers, YearSnapshot } from '../types';
import { simulate as simulateLocal } from '../utils/simulation';
import { simulateRemote } from '../api/client';

export interface Scenario {
  id: string;
  name: string;
  country: string;               // ← NEW
  levers: Levers;
  history: YearSnapshot[];
}

type Source = 'backend' | 'local' | null;

interface SimState {
  country: string;                          // ← NEW
  initialStocks: Record<string, number>;    // ← NEW
  levers: Levers;
  year: number;
  running: boolean;
  history: YearSnapshot[];
  source: Source;
  lastError: string | null;
  scenarios: Scenario[];
  setCountry: (c: string) => void;          // ← NEW
  setLever: (k: keyof Levers, v: number) => void;
  setYear: (y: number) => void;
  runSim: () => Promise<void>;
  saveScenario: (name: string) => void;
  loadScenario: (id: string) => void;
  deleteScenario: (id: string) => void;
}

const DEFAULT_LEVERS: Levers = {
  subsidy: 20, carbonTax: 10, offGrid: 30, gridExt: 30,
};

// Matches backend COUNTRY_PRESETS["IND"] so the Year-0 preview is accurate
// even before the first backend call lands.
const DEFAULT_INITIAL_STOCKS: Record<string, number> = {
  traditional: 1, lantern: 2, shs: 5, minigrid: 2, grid: 90,
};

export const useSimStore = create<SimState>((set, get) => ({
  country: 'IND',
  initialStocks: DEFAULT_INITIAL_STOCKS,
  levers: DEFAULT_LEVERS,
  year: 2026,
  running: false,
  history: simulateLocal(DEFAULT_LEVERS),
  source: 'local',
  lastError: null,
  scenarios: [],

  setCountry: (c) => set({ country: c.toUpperCase() }),
  setLever: (k, v) => set((s) => ({ levers: { ...s.levers, [k]: v } })),
  setYear: (year) => set({ year }),

  runSim: async () => {
    const { levers, country } = get();
    set({ running: true, lastError: null });

    try {
      const res = await simulateRemote(levers, country, 2026, 25);
      set({
        history: res.history,
        initialStocks: res.initialStocks,
        running: false,
        source: 'backend',
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Backend unavailable';
      console.warn('[sim] backend failed, using local fallback:', msg);
      set({
        history: simulateLocal(levers),
        running: false,
        source: 'local',
        lastError: msg,
      });
    }
  },

  saveScenario: (name) => {
    const { levers, history, country } = get();
    set((s) => ({
      scenarios: [
        ...s.scenarios,
        { id: Date.now().toString(), name, country, levers: { ...levers }, history: [...history] },
      ],
    }));
  },

  loadScenario: (id) => {
    const sc = get().scenarios.find((s) => s.id === id);
    if (sc) set({ levers: sc.levers, history: sc.history, country: sc.country, source: 'local' });
  },

  deleteScenario: (id) =>
    set((s) => ({ scenarios: s.scenarios.filter((x) => x.id !== id) })),
}));