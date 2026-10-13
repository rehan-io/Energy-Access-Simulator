import { create } from 'zustand';
import type { Levers, YearSnapshot } from '../types';
import { simulate } from '../utils/simulation';

export interface Scenario {
  id: string;
  name: string;
  levers: Levers;
  history: YearSnapshot[];
}

interface SimState {
  levers: Levers;
  year: number;
  running: boolean;
  history: YearSnapshot[];
  scenarios: Scenario[];
  setLever: (k: keyof Levers, v: number) => void;
  setYear: (y: number) => void;
  runSim: () => void;
  saveScenario: (name: string) => void;
  loadScenario: (id: string) => void;
  deleteScenario: (id: string) => void;
}

const DEFAULT_LEVERS: Levers = { subsidy: 20, carbonTax: 10, offGrid: 30, gridExt: 30 };

export const useSimStore = create<SimState>((set, get) => ({
  levers: DEFAULT_LEVERS,
  year: 2026,
  running: false,
  history: simulate(DEFAULT_LEVERS),
  scenarios: [],
  setLever: (k, v) => set((s) => ({ levers: { ...s.levers, [k]: v } })),
  setYear: (year) => set({ year }),
  runSim: () => {
    const { levers } = get();
    set({ running: true });
    setTimeout(() => set({ history: simulate(levers), running: false }), 350);
  },
  saveScenario: (name) => {
    const { levers, history } = get();
    set((s) => ({
      scenarios: [...s.scenarios, { id: Date.now().toString(), name, levers: { ...levers }, history: [...history] }],
    }));
  },
  loadScenario: (id) => {
    const sc = get().scenarios.find((s) => s.id === id);
    if (sc) set({ levers: sc.levers, history: sc.history });
  },
  deleteScenario: (id) => set((s) => ({ scenarios: s.scenarios.filter((x) => x.id !== id) })),
}));