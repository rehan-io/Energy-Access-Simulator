export type TierKey = 'traditional' | 'lantern' | 'shs' | 'minigrid' | 'grid';

export interface CountryOption {
  code: string;
  name: string;
  flag: string;
  access: number;
}

export interface Levers {
  subsidy: number;    // 0–100
  carbonTax: number;  // 0–100
  offGrid: number;    // 0–100
  gridExt: number;    // 0–100
}

export interface YearSnapshot {
  year: number;
  traditional: number;
  lantern: number;
  shs: number;
  minigrid: number;
  grid: number;
}

export interface StateData {
  id: string;
  name: string;
  lat: number;
  lng: number;
  population: number;    // millions
  initialAccess: number; // %
  solarPotential: number;
}