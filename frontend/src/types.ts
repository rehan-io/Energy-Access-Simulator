export const ACCESS_INDICATORS = [
  'elec_access_total',
  'elec_access_rural',
  'elec_access_urban',
  'clean_cooking_access',
] as const;

export type AccessIndicator = (typeof ACCESS_INDICATORS)[number];

export const ENERGY_TIERS = [
  'traditional',
  'lantern',
  'shs',
  'minigrid',
  'grid',
] as const;

export type EnergyTierKey = (typeof ENERGY_TIERS)[number];

export type HistoryKind = 'historical' | 'projected';

export interface YearSnapshot {
  year: number;
  kind: HistoryKind;
  elec_access_total: number | null;
  elec_access_rural: number | null;
  elec_access_urban: number | null;
  clean_cooking_access: number | null;
  traditional?: number | null;
  lantern?: number | null;
  shs?: number | null;
  minigrid?: number | null;
  grid?: number | null;
}

export interface TrendSummary {
  latest_year: number;
  latest_value: number;
  annual_trend: number;
  observations_used: number;
  window: number;
  first_year_used: number;
  last_year_used: number;
}

export type TrendMetadata = Record<AccessIndicator, TrendSummary>;

export type PolicyAdjustments = Partial<
  Record<AccessIndicator, number>
>;

export interface PolicyLevers {
  subsidy: number;
  carbon_tax: number;
  off_grid: number;
  grid_ext: number;
  recycle_tax_revenue: boolean;
}

export type PolicyLeverNumericKey =
  | 'subsidy'
  | 'carbon_tax'
  | 'off_grid'
  | 'grid_ext';

export interface CountryOption {
  code: string;
  name: string;
  access: number | null;
  cleanCookingAccess: number | null;
  baselineYear: number;
}

export interface SimulationRequest {
  country: string;
  years: number;
  trendWindow: number;
  policyLevers?: PolicyLevers;
  policyAdjustments?: PolicyAdjustments;
}

export interface SimulationResponse {
  countryCode: string;
  baselineYear: number;
  trendWindow: number;
  trends: TrendMetadata;
  policyAdjustments: PolicyAdjustments;
  policyLevers?: PolicyLevers;
  modelMode?: 'coupled' | 'linear_legacy';
  history: YearSnapshot[];
}

export interface BaselineResponse {
  countryCode: string;
  baselineYear: number;
  trendWindow: number;
  trends: TrendMetadata;
  historical: YearSnapshot[];
}