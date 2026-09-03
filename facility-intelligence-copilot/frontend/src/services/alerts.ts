import { apiGet, apiPatch } from './api';
import type { Alert } from '../types';

export async function getAlerts(): Promise<Alert[]> {
  return apiGet<Alert[]>('/api/v1/alerts');
}

export async function getAssetAlerts(assetId: number): Promise<Alert[]> {
  return apiGet<Alert[]>(`/api/v1/assets/${assetId}/alerts`);
}

export async function updateAlertStatus(alertId: number, status: string): Promise<Alert> {
  return apiPatch<Alert>(`/api/v1/alerts/${alertId}/status`, { status });
}
