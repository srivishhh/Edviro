import { apiGet, API_BASE_URL } from './api';
import type { InvestigationResult } from '../types';

export async function createInvestigation(assetId: number, alertId: number): Promise<InvestigationResult> {
  const url = `${API_BASE_URL}/api/v1/xray/investigations`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ asset_id: assetId, alert_id: alertId }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export async function getInvestigation(investigationId: string): Promise<InvestigationResult> {
  return apiGet<InvestigationResult>(`/api/v1/xray/investigations/${investigationId}`);
}
