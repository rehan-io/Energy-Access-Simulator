import { create } from 'zustand';
import type {
  CountryOption,
  PolicyLeverNumericKey,
  PolicyLevers,
  SimulationResponse,
  TrendMetadata,
  YearSnapshot,
} from '../types';
import { fetchCountries, fetchSimulation } from '../services/api';

export interface Scenario {
  id: string;
  name: string;
  country: string;
  years: number;
  trendWindow: number;
  policyLevers: PolicyLevers;
  result: SimulationResponse;
}

interface SimState {
  country: string;
  countries: CountryOption[];
  years: number;
  trendWindow: number;
  policyLevers: PolicyLevers;

  selectedYear: number | null;
  baselineYear: number | null;
  history: YearSnapshot[];
  trends: TrendMetadata | null;

  running: boolean;
  error: string | null;
  scenarios: Scenario[];

  initCountries: () => Promise<void>;
  setCountry: (country: string) => void;
  setYears: (years: number) => void;
  setTrendWindow: (window: number) => void;
  setPolicyLever: (lever: PolicyLeverNumericKey, value: number) => void;
  setRecycleTaxRevenue: (enabled: boolean) => void;
  resetPolicyLevers: () => void;
  setSelectedYear: (year: number) => void;

  runSim: () => Promise<void>;
  saveScenario: (name: string) => void;
  loadScenario: (id: string) => void;
  deleteScenario: (id: string) => void;
}

export const DEFAULT_POLICY_LEVERS: PolicyLevers = {
  subsidy: 0,
  carbon_tax: 0,
  off_grid: 0,
  grid_ext: 0,
  recycle_tax_revenue: true,
};

export const useSimStore = create<SimState>((set, get) => ({
  country: 'IND',
  countries: [],
  years: 25,
  trendWindow: 10,
  policyLevers: { ...DEFAULT_POLICY_LEVERS },

  selectedYear: null,
  baselineYear: null,
  history: [],
  trends: null,

  running: false,
  error: null,
  scenarios: [],

  initCountries: async () => {
    try {
      const countries = await fetchCountries();
      set({ countries, error: null });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Could not load countries';
      set({ error: message });
    }
  },

  setCountry: (country) => {
    set({
      country,
      history: [],
      trends: null,
      baselineYear: null,
      selectedYear: null,
      error: null,
    });

    void get().runSim();
  },

  setYears: (years) => set({ years }),

  setTrendWindow: (trendWindow) => set({ trendWindow }),

  setPolicyLever: (lever, value) =>
    set((state) => ({
      policyLevers: {
        ...state.policyLevers,
        [lever]: value,
      },
    })),

  setRecycleTaxRevenue: (enabled) =>
    set((state) => ({
      policyLevers: {
        ...state.policyLevers,
        recycle_tax_revenue: enabled,
      },
    })),

  resetPolicyLevers: () =>
    set({ policyLevers: { ...DEFAULT_POLICY_LEVERS } }),

  setSelectedYear: (selectedYear) => set({ selectedYear }),

  runSim: async () => {
    const { country, years, trendWindow, policyLevers } = get();

    set({ running: true, error: null });

    try {
      const result = await fetchSimulation({
        country,
        years,
        trendWindow,
        policyLevers,
      });

      set({
        history: result.history,
        trends: result.trends,
        baselineYear: result.baselineYear,
        selectedYear: result.baselineYear,
        running: false,
        error: null,
      });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Simulation failed';

      set({
        running: false,
        error: message,
        history: [],
        trends: null,
        baselineYear: null,
        selectedYear: null,
      });
    }
  },

  saveScenario: (name) => {
    const state = get();

    if (
      !state.history.length ||
      !state.trends ||
      state.baselineYear === null
    ) {
      return;
    }

    const result: SimulationResponse = {
      countryCode: state.country,
      baselineYear: state.baselineYear,
      trendWindow: state.trendWindow,
      trends: state.trends,
      policyAdjustments: {},
      policyLevers: { ...state.policyLevers },
      modelMode: 'coupled',
      history: [...state.history],
    };

    const scenario: Scenario = {
      id: Date.now().toString(),
      name,
      country: state.country,
      years: state.years,
      trendWindow: state.trendWindow,
      policyLevers: { ...state.policyLevers },
      result,
    };

    set((current) => ({
      scenarios: [...current.scenarios, scenario],
    }));
  },

  loadScenario: (id) => {
    const scenario = get().scenarios.find((item) => item.id === id);

    if (!scenario) return;

    set({
      country: scenario.country,
      years: scenario.years,
      trendWindow: scenario.trendWindow,
      policyLevers: { ...scenario.policyLevers },
      history: [...scenario.result.history],
      trends: scenario.result.trends,
      baselineYear: scenario.result.baselineYear,
      selectedYear: scenario.result.baselineYear,
      error: null,
    });
  },

  deleteScenario: (id) =>
    set((state) => ({
      scenarios: state.scenarios.filter((item) => item.id !== id),
    })),
}));