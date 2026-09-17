from __future__ import annotations

from typing import Dict, Any, List
from backend.counterfactual.schemas import (
    CandidatePlan,
    CounterfactualSimulationResult,
    ValidationStatus,
    ProvenanceType,
)
from backend.counterfactual.constraints import ConstraintChecker


class CounterfactualEvaluator:
    """
    Evaluates simulated branch states against deterministic constraints and safety baselines.
    """

    @classmethod
    def evaluate(
        cls,
        current_state: Dict[str, float],
        candidate: CandidatePlan,
        sim_output: Dict[str, Any],
    ) -> CounterfactualSimulationResult:
        predicted_state = sim_output["predicted_state"]
        deltas = sim_output.get("deltas", {})
        
        status, violations, score = ConstraintChecker.evaluate_constraints(
            current_state=current_state,
            interventions=candidate.interventions,
            predicted_state=predicted_state,
        )

        cur_power = current_state.get("power", 8.5)
        pred_power = predicted_state.get("power", cur_power)
        energy_saved_kw = round(cur_power - pred_power, 2)
        energy_saved_pct = round(100.0 * energy_saved_kw / max(cur_power, 0.1), 1)

        cur_zone_t = current_state.get("zone_temp", 22.8)
        pred_zone_t = predicted_state.get("zone_temp", cur_zone_t)
        comfort_delta_c = round(pred_zone_t - cur_zone_t, 2)

        # Build human-readable validation summary
        if status == ValidationStatus.VALIDATED:
            summary = f"Validated. Projected energy savings: {energy_saved_pct}% ({energy_saved_kw} kW). Zone comfort maintained at {pred_zone_t:.1f}°C."
        elif status == ValidationStatus.REJECTED:
            v_desc = ", ".join([v.description for v in violations[:2]])
            summary = f"Rejected due to safety/comfort violation: {v_desc}"
        else:
            summary = f"Needs Review: Partial violation detected ({violations[0].description if violations else 'Caution required'})."

        audit_prov = {
            "telemetry_source": ProvenanceType.SOURCE_FACT,
            "prediction_engine": ProvenanceType.MODEL_PREDICTION,
            "constraint_verification": ProvenanceType.DETERMINISTIC_CALCULATION,
        }

        return CounterfactualSimulationResult(
            candidate_id=candidate.candidate_id,
            title=candidate.title,
            status=status,
            score=score,
            proposed_interventions=candidate.interventions,
            predicted_state=predicted_state,
            deltas=deltas,
            violations=violations,
            energy_saved_kw=energy_saved_kw,
            energy_saved_pct=energy_saved_pct,
            comfort_delta_c=comfort_delta_c,
            audit_provenance=audit_prov,
            validation_summary=summary,
        )
