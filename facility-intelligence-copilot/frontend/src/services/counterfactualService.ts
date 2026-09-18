// ============================================================
// GSENSE 3.0 Counterfactual Service
// ============================================================

export interface ConstraintViolation {
  constraint_name: string;
  description: string;
  metric: string;
  actual_value: number;
  allowed_limit: string;
  severity: string;
}

export interface SafetyResult {
  status: 'PASS' | 'FAIL';
  violations: ConstraintViolation[];
}

export interface ResolutionResult {
  status: 'RESOLVES_ISSUE' | 'DOES_NOT_RESOLVE' | 'UNSAFE' | 'NEEDS_REVIEW';
  evidence: string[];
}

/** A single SNS candidate action (pre-simulation) */
export interface SNSCandidateAction {
  action_id: string;
  target: string;
  parameter: string;
  current_value: number;
  proposed_value: number;
  reason: string;
  expected_objective: string;
}

/** One Digital Twin simulation result per candidate */
export interface CounterfactualCandidate {
  candidate_id: string;
  title: string;
  status: 'VALIDATED' | 'REJECTED' | 'NEEDS_REVIEW';
  score: number;
  proposed_interventions: Record<string, number>;
  predicted_state: Record<string, number>;
  baseline_state?: Record<string, number>;
  deltas: {
    delta_zone_temp?: number;
    delta_power_kw?: number;
    energy_saved_pct?: number;
    delta_sa_cfm?: number;
    [key: string]: number | undefined;
  };
  safety?: SafetyResult;
  resolution?: ResolutionResult;
  violations: ConstraintViolation[];
  energy_saved_kw: number;
  energy_saved_pct: number;
  comfort_delta_c: number;
  audit_provenance: Record<string, string>;
  validation_summary: string;
}

export interface CounterfactualSolution {
  incident_id: string | null;
  timestamp: string;
  asset_id: string;
  fault_diagnosis: string;
  current_telemetry: Record<string, number>;
  candidates_evaluated: number;
  winning_candidate: CounterfactualCandidate | null;
  all_candidates: CounterfactualCandidate[];
  status?: string;
  reason?: string;
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
  counterfactual_solution: CounterfactualSolution;
  last_updated: string;
}

/** Full /investigate response — 3.0 GSense workflow with independent simulation branches */
export interface InvestigateResponse {
  incident_id: string;
  detected_fault: string;
  fault_confidence: number;
  sns: {
    workflow_name: string;
    workflow_id: string;
    execution_id: string;
    status: string;
    candidates_generated: number;
    candidate_actions: SNSCandidateAction[];
    diagnosis: {
      fault?: string;
      confidence?: number;
      evidence?: string[];
    };
  };
  simulation_summary: {
    total_simulated: number;
    safe: number;
    resolves: number;
    validated: number;
  };
  simulations: CounterfactualCandidate[];
  validated_intervention: CounterfactualCandidate | null;
  status: 'VALIDATED' | 'NO_VALIDATED_INTERVENTION';
  reason: string;
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

  /**
   * Runs the full GSENSE 3.0 pipeline for a specific incident:
   * SNS 3.0 GSense → 6-8 independent candidates → Digital Twin simulations → validated result
   */
  async runInvestigation(incidentId: string, payload?: {
    asset_id?: string;
    detected_fault?: string;
    current_telemetry?: Record<string, number>;
  }): Promise<InvestigateResponse> {
    const res = await fetch(`${API_BASE}/api/v1/incidents/${incidentId}/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {}),
    });
    if (!res.ok) {
      throw new Error(`Investigation failed: ${res.statusText}`);
    }
    return res.json();
  },

  async evaluateCounterfactual(payload: {
    asset_id?: string;
    current_telemetry?: Record<string, number>;
    incident_id?: string;
    sns_proposed_plan?: Record<string, unknown>;
  }): Promise<CounterfactualSolution> {
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
  }): Promise<{ success: boolean; message: string; actuation_record: Record<string, unknown> }> {
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
