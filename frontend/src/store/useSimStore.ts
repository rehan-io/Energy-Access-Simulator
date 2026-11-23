
import { create } from 'zustand';
import type {
  AccessIndicator,
  CountryOption,
  PolicyAdjustments,
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
  policyAdjustments: PolicyAdjustments;
  result: SimulationResponse;
}

interface SimState {
  country: string;
  countries: CountryOption[];
  years: number;
  trendWindow: number;
  policyAdjustments: PolicyAdjustments;

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
  setPolicyAdjustment: (
    indicator: AccessIndicator,
    value: number,
  ) => void;
  setSelectedYear: (year: number) => void;

  runSim: () => Promise<void>;
  saveScenario: (name: string) => void;
  loadScenario: (id: string) => void;
  deleteScenario: (id: string) => void;
}

const DEFAULT_POLICY_ADJUSTMENTS: PolicyAdjustments = {
  elec_access_total: 0,
  elec_access_rural: 0,
  elec_access_urban: 0,
  clean_cooking_access: 0,
};

export const useSimStore = create<SimState>((set, get) => ({
  country: 'IND',
  countries: [],
  years: 25,
  trendWindow: 10,
  policyAdjustments: { ...DEFAULT_POLICY_ADJUSTMENTS },

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

  setPolicyAdjustment: (indicator, value) =>
    set((state) => ({
      policyAdjustments: {
        ...state.policyAdjustments,
        [indicator]: value,
      },
    })),

  setSelectedYear: (selectedYear) => set({ selectedYear }),

  runSim: async () => {
    const { country, years, trendWindow, policyAdjustments } = get();

    set({ running: true, error: null });

    try {
      const result = await fetchSimulation({
        country,
        years,
        trendWindow,
        policyAdjustments,
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
      policyAdjustments: { ...state.policyAdjustments },
      history: [...state.history],
    };

    const scenario: Scenario = {
      id: Date.now().toString(),
      name,
      country: state.country,
      years: state.years,
      trendWindow: state.trendWindow,
      policyAdjustments: { ...state.policyAdjustments },
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
      policyAdjustments: { ...scenario.policyAdjustments },
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
