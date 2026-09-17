from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProvenanceType(str, Enum):
    SOURCE_FACT = "SOURCE_FACT"
    MODEL_PREDICTION = "MODEL_PREDICTION"
    DETERMINISTIC_CALCULATION = "DETERMINISTIC_CALCULATION"
    LLM_REASONING = "LLM_REASONING"


class ValidationStatus(str, Enum):
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ResolutionStatus(str, Enum):
    RESOLVES_ISSUE = "RESOLVES_ISSUE"
    DOES_NOT_RESOLVE = "DOES_NOT_RESOLVE"
    UNSAFE = "UNSAFE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ProvenancedValue(BaseModel):
    value: Any
    provenance: ProvenanceType
    source_detail: Optional[str] = None


class ActuatorIntervention(BaseModel):
    actuator: str = Field(..., description="Target actuator, e.g. 'oa_dmpr', 'sf_spd', 'chwc_vlv'")
    current_value: float = 0.0
    target_value: float = 0.0
    unit: str = "%"


class CandidateAction(BaseModel):
    action_id: str
    target: str = Field(..., description="Target actuator, e.g. 'oa_dmpr', 'sf_spd', 'chwc_vlv'")
    parameter: str = "value"
    current_value: float = 0.0
    proposed_value: float = 0.0
    reason: Optional[str] = None
    expected_objective: Optional[str] = None



class CandidatePlan(BaseModel):
    candidate_id: str
    title: str
    description: str
    proposed_by: str = Field("SNS_COGNITIVE_AGENT", description="Source of candidate: SNS_COGNITIVE_AGENT, RULE_ENGINE, OPERATOR")
    interventions: Dict[str, float] = Field(..., description="Map of actuator names to proposed values")
    actions: List[CandidateAction] = Field(default_factory=list)
    expected_rationale: Optional[str] = None


class ConstraintViolation(BaseModel):
    constraint_name: str
    description: str
    metric: str
    actual_value: float
    allowed_limit: str
    severity: str = "CRITICAL"


class SafetyResult(BaseModel):
    status: str = Field("PASS", description="PASS or FAIL")
    violations: List[ConstraintViolation] = Field(default_factory=list)


class ResolutionResult(BaseModel):
    status: ResolutionStatus = ResolutionStatus.RESOLVES_ISSUE
    evidence: List[str] = Field(default_factory=list)


class CounterfactualSimulationResult(BaseModel):
    candidate_id: str
    title: str
    status: ValidationStatus
    score: float = Field(..., description="Overall confidence and fitness score from 0.0 to 1.0")
    proposed_interventions: Dict[str, float]
    actions: List[CandidateAction] = Field(default_factory=list)
    baseline_state: Dict[str, float] = Field(default_factory=dict)
    predicted_state: Dict[str, float]
    deltas: Dict[str, float] = Field(default_factory=dict)
    safety: SafetyResult = Field(default_factory=SafetyResult)
    resolution: ResolutionResult = Field(default_factory=ResolutionResult)
    violations: List[ConstraintViolation] = Field(default_factory=list)
    energy_saved_kw: float = 0.0
    energy_saved_pct: float = 0.0
    comfort_delta_c: float = 0.0
    audit_provenance: Dict[str, ProvenanceType] = Field(default_factory=dict)
    validation_summary: str = ""


class CounterfactualEvaluationResponse(BaseModel):
    incident_id: Optional[str] = None
    timestamp: str
    asset_id: str
    fault_diagnosis: str
    current_telemetry: Dict[str, float]
    candidates_evaluated: int
    winning_candidate: Optional[CounterfactualSimulationResult] = None
    all_candidates: List[CounterfactualSimulationResult]
    status: str = "VALIDATED"
    reason: Optional[str] = None

