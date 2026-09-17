from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Any

from backend.counterfactual.schemas import (
    CandidatePlan,
    CounterfactualEvaluationResponse,
    CounterfactualSimulationResult,
    ValidationStatus,
)
from backend.counterfactual.candidate_generator import CandidateGenerator
from backend.counterfactual.simulator import CounterfactualSimulator
from backend.counterfactual.evaluator import CounterfactualEvaluator
from backend.ml.features.feature_engineering import canonicalize_telemetry_dict

logger = logging.getLogger(__name__)


class CounterfactualEngine:
    """
    GSENSE 3.0 Counterfactual Intelligence and Verification Engine.
    Executes real ML state simulations and deterministic constraint checks on candidate solutions.
    """
    _instance: Optional["CounterfactualEngine"] = None

    def __init__(self):
        self.simulator = CounterfactualSimulator()

    @classmethod
    def get_instance(cls) -> "CounterfactualEngine":
        if cls._instance is None:
            cls._instance = CounterfactualEngine()
        return cls._instance

    def evaluate_facility_state(
        self,
        asset_id: str,
        current_telemetry: Dict[str, Any],
        fault_diagnosis: str = "nominal",
        incident_id: Optional[str] = None,
        sns_proposed_plan: Optional[Dict[str, Any]] = None,
    ) -> CounterfactualEvaluationResponse:
        """
        Orchestrates full counterfactual evaluation workflow for an incident or current asset state.
        """
        canonical_telemetry = canonicalize_telemetry_dict(current_telemetry)
        
        # 1. Generate Candidates
        candidates = CandidateGenerator.generate_candidates(
            fault_class=fault_diagnosis,
            current_telemetry=canonical_telemetry,
            sns_proposed_plan=sns_proposed_plan,
        )

        evaluated_results: List[CounterfactualSimulationResult] = []

        # 2. Simulate & Evaluate each candidate
        for cand in candidates:
            try:
                sim_out = self.simulator.simulate_candidate(
                    current_state=canonical_telemetry,
                    candidate=cand,
                )
                eval_res = CounterfactualEvaluator.evaluate(
                    current_state=canonical_telemetry,
                    candidate=cand,
                    sim_output=sim_out,
                )
                evaluated_results.append(eval_res)
            except Exception as e:
                logger.error(f"Failed to evaluate candidate {cand.candidate_id}: {e}")

        # 3. Sort candidates: VALIDATED (highest score) -> NEEDS_REVIEW -> REJECTED
        def sort_key(item: CounterfactualSimulationResult):
            status_priority = {
                ValidationStatus.VALIDATED: 3,
                ValidationStatus.NEEDS_REVIEW: 2,
                ValidationStatus.REJECTED: 1,
            }
            return (status_priority.get(item.status, 0), item.score)

        evaluated_results.sort(key=sort_key, reverse=True)

        # 4. Pick winning candidate (top VALIDATED result)
        winning_candidate = next(
            (r for r in evaluated_results if r.status == ValidationStatus.VALIDATED),
            evaluated_results[0] if evaluated_results else None,
        )

        return CounterfactualEvaluationResponse(
            incident_id=incident_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            asset_id=asset_id,
            fault_diagnosis=fault_diagnosis,
            current_telemetry=canonical_telemetry,
            candidates_evaluated=len(evaluated_results),
            winning_candidate=winning_candidate,
            all_candidates=evaluated_results,
        )
