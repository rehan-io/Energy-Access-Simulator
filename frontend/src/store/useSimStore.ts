import { create } from 'zustand';
import type { Levers, YearSnapshot, CountryOption, TierKey } from '../types';
import { simulate, DUMMY_COUNTRY_STOCKS } from '../utils/simulation';
import { fetchSimulation, fetchCountries } from '../services/api';

export interface Scenario {
  id: string;
  name: string;
  country: string;
  levers: Levers;
  history: YearSnapshot[];
}

interface SimState {
  country: string;
  countries: CountryOption[];
  initialStocks: Record<TierKey, number>;
  levers: Levers;
  year: number;
  running: boolean;
  history: YearSnapshot[];
  scenarios: Scenario[];
  setCountry: (country: string) => void;
  setLever: (k: keyof Levers, v: number) => void;
  setYear: (y: number) => void;
  runSim: () => Promise<void>;
  initCountries: () => Promise<void>;
  saveScenario: (name: string) => void;
  loadScenario: (id: string) => void;
  deleteScenario: (id: string) => void;
}

const DEFAULT_LEVERS: Levers = { subsidy: 20, carbonTax: 10, offGrid: 30, gridExt: 30 };

const DEFAULT_COUNTRIES: CountryOption[] = [
  { code: 'IND', name: 'India', flag: '🇮🇳', access: 99.6 },
  { code: 'KEN', name: 'Kenya', flag: '🇰🇪', access: 77.0 },
  { code: 'RWA', name: 'Rwanda', flag: '🇷🇼', access: 72.4 },
  { code: 'NGA', name: 'Nigeria', flag: '🇳🇬', access: 59.5 },
];

export const useSimStore = create<SimState>((set, get) => ({
  country: 'IND',
  countries: DEFAULT_COUNTRIES,
  initialStocks: DUMMY_COUNTRY_STOCKS.IND,
  levers: DEFAULT_LEVERS,
  year: 2026,
  running: false,
  history: simulate(DEFAULT_LEVERS, 'IND'),
  scenarios: [],

  initCountries: async () => {
    try {
      const countries = await fetchCountries();
      set({ countries });
    } catch {
      // Keep DEFAULT_COUNTRIES fallback
    }
  },

  setCountry: (country: string) => {
    const { levers } = get();
    const stocks = DUMMY_COUNTRY_STOCKS[country] || DUMMY_COUNTRY_STOCKS.IND;
    set({
      country,
      initialStocks: stocks,
      history: simulate(levers, country),
    });
    // Trigger simulation with new country
    get().runSim();
  },

  setLever: (k, v) => set((s) => ({ levers: { ...s.levers, [k]: v } })),
  setYear: (year) => set({ year }),

  runSim: async () => {
    const { levers, country } = get();
    set({ running: true });
    try {
      const data = await fetchSimulation(levers, country);
      set({
        history: data.history,
        initialStocks: data.initialStocks || DUMMY_COUNTRY_STOCKS[country],
        running: false,
      });
    } catch (err) {
      console.warn('Backend unavailable, running client simulation:', err);
      set({ history: simulate(levers, country), running: false });
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
      set({
        country: sc.country,
        initialStocks: DUMMY_COUNTRY_STOCKS[sc.country] || DUMMY_COUNTRY_STOCKS.IND,
        levers: sc.levers,
        history: sc.history,
      });
    }
  },
  deleteScenario: (id) => set((s) => ({ scenarios: s.scenarios.filter((x) => x.id !== id) })),
}));