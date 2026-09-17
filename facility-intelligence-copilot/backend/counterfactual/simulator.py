from __future__ import annotations

from typing import Dict, Any
from backend.ml.inference.state_predictor import StatePredictor
from backend.counterfactual.schemas import CandidatePlan, ProvenanceType


class CounterfactualSimulator:
    """
    Executes counterfactual branch execution through the StatePredictor ML surrogate.
    """

    def __init__(self):
        self.state_predictor = StatePredictor.get_instance()

    def simulate_candidate(
        self,
        current_state: Dict[str, float],
        candidate: CandidatePlan,
    ) -> Dict[str, Any]:
        """
        Simulates the effect of applying candidate interventions to current physical state.
        """
        sim_result = self.state_predictor.predict_counterfactual(
            current_state=current_state,
            interventions=candidate.interventions,
        )
        
        # Provenance attribution
        provenance = {
            "current_state": ProvenanceType.SOURCE_FACT,
            "proposed_interventions": ProvenanceType.LLM_REASONING if candidate.proposed_by == "SNS_COGNITIVE_AGENT" else ProvenanceType.DETERMINISTIC_CALCULATION,
            "predicted_metrics": ProvenanceType.MODEL_PREDICTION,
            "deltas": ProvenanceType.DETERMINISTIC_CALCULATION,
        }

        return {
            "candidate_id": candidate.candidate_id,
            "title": candidate.title,
            "description": candidate.description,
            "proposed_interventions": candidate.interventions,
            "predicted_state": sim_result["predicted_state"],
            "predicted_metrics": sim_result["predicted_metrics"],
            "deltas": sim_result["deltas"],
            "provenance": provenance,
        }
