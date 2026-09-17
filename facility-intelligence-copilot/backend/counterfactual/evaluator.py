from __future__ import annotations

from typing import Dict, Any, List, Optional
from backend.counterfactual.schemas import (
    CandidatePlan,
    CounterfactualSimulationResult,
    ValidationStatus,
    ResolutionStatus,
    SafetyResult,
    ResolutionResult,
    ProvenanceType,
)
from backend.counterfactual.constraints import ConstraintChecker
from backend.counterfactual.resolution import ResolutionEvaluator


class CounterfactualEvaluator:
    """
    Evaluates simulated branch states against deterministic safety constraints
    and fault-specific resolution criteria.
    """

    @classmethod
    def evaluate(
        cls,
        current_state: Dict[str, float],
        candidate: CandidatePlan,
        sim_output: Dict[str, Any],
        detected_fault: str = "nominal",
    ) -> CounterfactualSimulationResult:
        predicted_state = sim_output.get("predicted_state", current_state)
        deltas = sim_output.get("deltas", {})
        
        # 1. Deterministic Safety Constraint Verification
        safety_status, violations, safety_score = ConstraintChecker.evaluate_constraints(
            current_state=current_state,
            interventions=candidate.interventions,
            predicted_state=predicted_state,
        )
        is_safe = len(violations) == 0

        # 2. Deterministic Fault Resolution Verification
        res_status, res_evidence = ResolutionEvaluator.evaluate_resolution(
            detected_fault=detected_fault,
            baseline_state=current_state,
            predicted_state=predicted_state,
            is_safe=is_safe,
        )

        # 3. Overall Candidate Validation Decision
        if not is_safe:
            status = ValidationStatus.REJECTED
            score = max(0.0, safety_score * 0.5)
        elif res_status == ResolutionStatus.RESOLVES_ISSUE:
            status = ValidationStatus.VALIDATED
            score = safety_score
        elif res_status == ResolutionStatus.DOES_NOT_RESOLVE:
            status = ValidationStatus.REJECTED
            score = max(0.1, safety_score * 0.6)
        else:
            status = ValidationStatus.NEEDS_REVIEW
            score = safety_score * 0.8

        cur_power = current_state.get("power", 8.5)
        pred_power = predicted_state.get("power", cur_power)
        energy_saved_kw = round(cur_power - pred_power, 2)
        energy_saved_pct = round(100.0 * energy_saved_kw / max(cur_power, 0.1), 1)

        cur_zone_t = current_state.get("zone_temp", 22.8)
        pred_zone_t = predicted_state.get("zone_temp", cur_zone_t)
        comfort_delta_c = round(pred_zone_t - cur_zone_t, 2)

        # 4. Human-readable Validation Summary
        if status == ValidationStatus.VALIDATED:
            summary = f"Validated: Resolves {detected_fault}. Comfort maintained ({pred_zone_t:.1f}°C). Energy savings: {energy_saved_pct}% ({energy_saved_kw} kW)."
        elif not is_safe:
            v_desc = ", ".join([v.description for v in violations[:2]])
            summary = f"Rejected: Safety/comfort constraint violation ({v_desc})."
        elif res_status == ResolutionStatus.DOES_NOT_RESOLVE:
            reason = res_evidence[0] if res_evidence else "Simulated state fails to resolve diagnosed fault condition."
            summary = f"Rejected: Does not resolve issue ({reason})."
        else:
            summary = f"Needs Review: Advisory review required before actuation."

        audit_prov = {
            "action_generation": ProvenanceType.LLM_REASONING if candidate.proposed_by == "SNS_COGNITIVE_AGENT" else ProvenanceType.DETERMINISTIC_CALCULATION,
            "telemetry_source": ProvenanceType.SOURCE_FACT,
            "state_prediction": ProvenanceType.MODEL_PREDICTION,
            "constraint_verification": ProvenanceType.DETERMINISTIC_CALCULATION,
            "resolution_verification": ProvenanceType.DETERMINISTIC_CALCULATION,
        }

        return CounterfactualSimulationResult(
            candidate_id=candidate.candidate_id,
            title=candidate.title,
            status=status,
            score=round(score, 3),
            proposed_interventions=candidate.interventions,
            actions=candidate.actions,
            baseline_state=current_state,
            predicted_state=predicted_state,
            deltas=deltas,
            safety=SafetyResult(status="PASS" if is_safe else "FAIL", violations=violations),
            resolution=ResolutionResult(status=res_status, evidence=res_evidence),
            violations=violations,
            energy_saved_kw=energy_saved_kw,
            energy_saved_pct=energy_saved_pct,
            comfort_delta_c=comfort_delta_c,
            audit_provenance=audit_prov,
            validation_summary=summary,
        )

