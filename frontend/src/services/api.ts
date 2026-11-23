
import type {
  BaselineResponse,
  CountryOption,
  SimulationRequest,
  SimulationResponse,
} from '../types';

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = response.statusText;

    try {
      const body = await response.json();
      detail =
        typeof body.detail === 'string'
          ? body.detail
          : JSON.stringify(body.detail ?? body);
    } catch {
      // Retain the HTTP status text if the response isn't JSON.
    }

    throw new Error(`API error (${response.status}): ${detail}`);
  }

  return response.json() as Promise<T>;
}

export async function fetchCountries(): Promise<CountryOption[]> {
  const response = await fetch('/api/countries');
  return parseResponse<CountryOption[]>(response);
}

export async function fetchSimulation(
  request: SimulationRequest,
): Promise<SimulationResponse> {
  const response = await fetch('/api/simulate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return parseResponse<SimulationResponse>(response);
}

export async function fetchBaseline(
  countryCode: string,
): Promise<BaselineResponse> {
  const response = await fetch(
    `/api/baseline/${encodeURIComponent(countryCode)}`,
  );

  return parseResponse<BaselineResponse>(response);
}
