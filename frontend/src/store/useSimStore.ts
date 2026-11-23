import { create } from 'zustand';
import type { Levers, YearSnapshot } from '../types';
import { simulate as simulateLocal } from '../utils/simulation';
import { simulateRemote } from '../api/client';

export interface Scenario {
  id: string;
  name: string;
  country: string;
  levers: Levers;
  history: YearSnapshot[];
}

type Source = 'backend' | 'local' | null;

interface SimState {
  country: string;
  initialStocks: Record<string, number>;
  levers: Levers;
  year: number;
  running: boolean;
  history: YearSnapshot[];
  referenceHistory: Record<string, YearSnapshot[]>;
  source: Source;
  lastError: string | null;
  scenarios: Scenario[];
  setCountry: (c: string) => Promise<void>;
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

const DEFAULT_INITIAL_STOCKS: Record<string, number> = {
  traditional: 15, lantern: 15, shs: 30, minigrid: 10, grid: 30,
};

// Simple debounce so fast slider drags don't flood the backend
let runTimer: ReturnType<typeof setTimeout> | null = null;

export const useSimStore = create<SimState>((set, get) => ({
  country: 'IND',
  initialStocks: DEFAULT_INITIAL_STOCKS,
  levers: DEFAULT_LEVERS,
  year: 2026,
  running: false,
  history: simulateLocal(DEFAULT_LEVERS, DEFAULT_INITIAL_STOCKS),
  referenceHistory: {},
  source: 'local',
  lastError: null,
  scenarios: [],

  setCountry: async (c) => {
    set({ country: c.toUpperCase(), initialStocks: DEFAULT_INITIAL_STOCKS });
    await get().runSim();
  },

  setLever: (k, v) => {
    set((s) => ({ levers: { ...s.levers, [k]: v } }));
    if (runTimer) clearTimeout(runTimer);
    runTimer = setTimeout(() => get().runSim(), 250);
  },

  setYear: (year) => set({ year }),

//   runSim: async () => {
//   const { levers, country, initialStocks, referenceHistory } = get();
//   set({ running: true, lastError: null });

//   try {
//     // Fetch/cache reference (default levers) for this country, once
//     let ref = referenceHistory[country];
//     if (!ref) {
//       const refRes = await simulateRemote(DEFAULT_LEVERS, country, 2026, 50);
//       ref = refRes.history;
//       set((s) => ({
//         referenceHistory: { ...s.referenceHistory, [country]: ref! },
//       }));
//     }

//     const res = await simulateRemote(levers, country, 2026, 50);
//     set({
//       history: res.history,
//       initialStocks: res.initialStocks,
//       running: false,
//       source: 'backend',
//     });
//   } catch (err: unknown) {
//     const msg = err instanceof Error ? err.message : 'Backend unreachable';
//     console.warn('[sim] fallback to local:', msg);
//     set({
//       history: simulateLocal(levers, initialStocks ?? DEFAULT_INITIAL_STOCKS, 2026, 50),
//       running: false,
//       source: 'local',
//       lastError: msg,
//     });
//   }
// },

runSim: async () => {
  const { levers, country, initialStocks, referenceHistory } = get();
  set({ running: true, lastError: null });

  const stocks = initialStocks ?? DEFAULT_INITIAL_STOCKS;

  try {
    // Fetch reference (default policy) once per country
    let ref = referenceHistory[country];
    if (!ref) {
      const refRes = await simulateRemote(DEFAULT_LEVERS, country, 2026, 50);
      ref = refRes.history;
    }

    // Fetch current policy run
    const res = await simulateRemote(levers, country, 2026, 50);

    set({
      history: res.history,
      initialStocks: res.initialStocks,
      referenceHistory: { ...referenceHistory, [country]: ref },
      running: false,
      source: 'backend',
    });
  } catch (err: unknown) {
    // Backend down → compute BOTH from local so the delta is consistent
    const msg = err instanceof Error ? err.message : 'Backend unreachable';
    console.warn('[sim] fallback to local:', msg);
    set({
      history: simulateLocal(levers, stocks, 2026, 50),
      referenceHistory: {
        ...referenceHistory,
        [country]: simulateLocal(DEFAULT_LEVERS, stocks, 2026, 50),
      },
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
    if (sc) {
      set({ levers: sc.levers, history: sc.history, country: sc.country, source: 'local' });
    }
  },

  deleteScenario: (id) =>
    set((s) => ({ scenarios: s.scenarios.filter((x) => x.id !== id) })),
}));