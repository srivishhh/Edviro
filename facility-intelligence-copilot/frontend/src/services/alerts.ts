import { apiGet } from './api';
import type { Alert } from '../types/alert';

export async function getAlerts(): Promise<Alert[]> {
    return apiGet<Alert[]>('/api/v1/alerts');
}

export async function getAssetAlerts(assetId: number): Promise<Alert[]> {
    return apiGet<Alert[]>(`/api/v1/assets/${assetId}/alerts`);
}
