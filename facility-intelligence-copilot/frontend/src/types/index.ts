export interface Asset {
  id: number;
  asset_code: string;
  name: string;
  asset_type: string;
  building_id: number | null;
  floor_id: number | null;
  manufacturer?: string | null;
  model?: string | null;
  installation_date?: string | null;
  status: string;
  health_score: number;
  created_at?: string;
  updated_at?: string;
}

export type AlertSeverity = 'CRITICAL' | 'HIGH' | 'WARNING' | 'INFO';
export type AlertStatus = 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';

export interface Alert {
  id: number;
  asset_id: number;
  alert_type: string;
  severity: AlertSeverity | string;
  message: string;
  anomaly_score: number;
  detected_at: string;
  status: AlertStatus | string;
}

export interface TelemetryPoint {
  timestamp: string;
  temperature: number;
  energy_kw: number;
  pressure: number;
  airflow: number;
}

export interface TwinRelationship {
  type: string;
  target: string;
}

export interface TwinCurrentState {
  temperature: number;
  energy_kw: number;
  pressure: number;
  airflow: number;
}

export interface TwinAsset {
  asset_id: number;
  status: string;
  health_score: number;
  current_state: TwinCurrentState;
  last_updated: string;
  relationships: TwinRelationship[];
}

export interface EvidenceItem {
  source: string;
  metric: string;
  value: number;
  baseline: number;
  expected_range: string;
  interpretation: string;
}

export interface InvestigationResult {
  investigation_id: string;
  asset_id: number;
  alert_id: number;
  status: string;
  summary: string;
  root_cause: string;
  confidence: string;
  severity: string;
  evidence: EvidenceItem[];
  observed: string[];
  inferred: string[];
  alternative_causes: string[];
  recommended_actions: string[];
  created_at: string;
}

export interface SystemStatus {
  backend: string;
  database: string;
  kafka: string;
  xray: string;
  simulator: string;
  timestamp: string;
}
