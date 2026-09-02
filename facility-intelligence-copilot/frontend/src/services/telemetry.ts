import { apiGet } from './api';
import type { TelemetryPoint } from '../types/telemetry';

export type TelemetryQuery = Record<string, string | number | boolean | undefined> & {
  limit?: number;
  from?: string;
  to?: string;
};

export async function getAssetTelemetry(assetId: number, params: TelemetryQuery = {}): Promise<TelemetryPoint[]> {
  return apiGet<TelemetryPoint[]>(`/api/v1/assets/${assetId}/telemetry`, params);
}
