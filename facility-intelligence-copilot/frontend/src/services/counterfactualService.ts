export interface ConstraintViolation {
  constraint_name: string;
  description: string;
  metric: string;
  actual_value: number;
  allowed_limit: string;
  severity: string;
}

export interface CounterfactualCandidate {
  candidate_id: string;
  title: string;
  status: 'VALIDATED' | 'REJECTED' | 'NEEDS_REVIEW';
  score: number;
  proposed_interventions: Record<string, number>;
  predicted_state: Record<string, number>;
  deltas: {
    delta_zone_temp?: number;
    delta_power_kw?: number;
    energy_saved_pct?: number;
    delta_sa_cfm?: number;
    [key: string]: number | undefined;
  };
  violations: ConstraintViolation[];
  energy_saved_kw: number;
  energy_saved_pct: number;
  comfort_delta_c: number;
  audit_provenance: Record<string, string>;
  validation_summary: string;
}

export interface ActiveIncidentResponse {
  has_active_incident: boolean;
  incident_id: string | null;
  asset_id: string;
  asset_name: string;
  facility_status: string;
  health_score: number;
  fault_diagnosis: string;
  fault_probability: number;
  confidence: string;
  indicators: string[];
  current_telemetry: Record<string, number>;
  counterfactual_solution: {
    incident_id: string | null;
    timestamp: string;
    asset_id: string;
    fault_diagnosis: string;
    current_telemetry: Record<string, number>;
    candidates_evaluated: number;
    winning_candidate: CounterfactualCandidate | null;
    all_candidates: CounterfactualCandidate[];
  };
  last_updated: string;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? import.meta.env.VITE_API_URL ?? '';

export const counterfactualService = {
  async getActiveIncident(): Promise<ActiveIncidentResponse> {
    const res = await fetch(`${API_BASE}/api/v1/incidents/active`);
    if (!res.ok) {
      throw new Error(`Failed to fetch active incident: ${res.statusText}`);
    }
    return res.json();
  },

  async evaluateCounterfactual(payload: {
    asset_id?: string;
    current_telemetry?: Record<string, number>;
    incident_id?: string;
    sns_proposed_plan?: any;
  }): Promise<ActiveIncidentResponse['counterfactual_solution']> {
    const res = await fetch(`${API_BASE}/api/v1/counterfactual/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error(`Counterfactual evaluation failed: ${res.statusText}`);
    }
    return res.json();
  },

  async applyActuation(payload: {
    candidate_id: string;
    interventions: Record<string, number>;
    asset_id?: string;
    notes?: string;
  }): Promise<{ success: boolean; message: string; actuation_record: any }> {
    const res = await fetch(`${API_BASE}/api/v1/incidents/actuate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error(`Actuation request failed: ${res.statusText}`);
    }
    return res.json();
  },
};
