import { API_BASE_URL } from './api';

export interface WhatIfParameterChanges {
  temperature?: number;
  pressure?: number;
  airflow?: number;
  energy_kw?: number;
}

export interface WhatIfSimulateRequest {
  asset_id: string | number;
  changes: WhatIfParameterChanges;
  scenario_preset?: string;
}

export interface WhatIfParameterState {
  temperature: number;
  pressure: number;
  airflow: number;
  energy_kw: number;
  health: number;
  risk: number;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
}

export interface WhatIfImpact {
  energy_change_kw: number;
  energy_change_percent: number;
  health_change: number;
  risk_change: number;
}

export interface WhatIfSimulateResponse {
  asset_id: string;
  asset_name: string;
  current: WhatIfParameterState;
  predicted: WhatIfParameterState;
  impact: WhatIfImpact;
  assessment: string;
  recommendations: string[];
  explanation: string;
  scenario_preset?: string;
  is_simulation: boolean;
}

export interface WhatIfPreset {
  id: string;
  name: string;
  description: string;
  changes: WhatIfParameterChanges;
  expected_outcome: string;
}

export async function simulateWhatIf(
  payload: WhatIfSimulateRequest
): Promise<WhatIfSimulateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/what-if/simulate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || errorData.message || `Simulation failed (HTTP ${response.status})`
    );
  }

  return response.json();
}

export async function getWhatIfPresets(): Promise<WhatIfPreset[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/what-if/presets`, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to load scenario presets (HTTP ${response.status})`);
  }

  return response.json();
}

export async function getCurrentAssetSimulationState(assetId: string | number): Promise<{
  asset_id: string;
  asset_name: string;
  current: WhatIfParameterState;
}> {
  const response = await fetch(`${API_BASE_URL}/api/v1/what-if/assets/${assetId}/current`, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to load asset state (HTTP ${response.status})`);
  }

  return response.json();
}
