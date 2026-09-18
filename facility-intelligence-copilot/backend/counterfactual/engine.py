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
    GSENSE 3.0 Counterfactual Intelligence and Virtual Twin Engine.

    INDEPENDENT BRANCH SIMULATION RULE:
    Every candidate is simulated starting from an immutable copy of the baseline telemetry.
    No candidate may mutate state that another candidate depends on.
    Candidates are NEVER merged before simulation.
    """
    _instance: Optional["CounterfactualEngine"] = None

    def __init__(self):
        self.simulator = CounterfactualSimulator()

    @classmethod
    def get_instance(cls) -> "CounterfactualEngine":
        if cls._instance is None:
            cls._instance = CounterfactualEngine()
        return cls._instance

    # ------------------------------------------------------------------
    # Primary API (new path): independent simulation of SNS candidates
    # ------------------------------------------------------------------

    def evaluate_with_sns_candidates(
        self,
        asset_id: str,
        current_telemetry: Dict[str, Any],
        fault_diagnosis: str,
        sns_candidate_actions: List[Dict[str, Any]],
        incident_id: Optional[str] = None,
    ) -> CounterfactualEvaluationResponse:
        """
        GSENSE 3.0 Primary Counterfactual Evaluation Path.

        Each SNS candidate_action → independent CandidatePlan → independent simulation.
        Baseline telemetry is copied fresh for EVERY simulation branch.
        No candidate affects any other candidate's simulation.

        SNS Candidate 1 → Twin Simulation 1
        SNS Candidate 2 → Twin Simulation 2
        ...
        SNS Candidate N → Twin Simulation N
        """
        canonical_telemetry = canonicalize_telemetry_dict(current_telemetry)

        # 1. Convert SNS candidates into independent CandidatePlans
        sns_plans = CandidateGenerator.from_sns_candidate_list(
            sns_candidate_actions=sns_candidate_actions,
            current_telemetry=canonical_telemetry,
        )

        # 2. Also generate domain analytical candidates for coverage
        domain_plans = CandidateGenerator.generate_candidates(
            fault_class=fault_diagnosis,
            current_telemetry=canonical_telemetry,
            sns_proposed_plan=None,  # no legacy merging
        )

        # Combine: SNS candidates first, then domain candidates
        # Deduplicate by intervention signature
        all_plans = self._merge_deduplicated(sns_plans, domain_plans)

        logger.info(
            f"[Engine] evaluate_with_sns_candidates: fault={fault_diagnosis} "
            f"sns={len(sns_plans)} domain={len(domain_plans)} total={len(all_plans)}"
        )

        # 3. Simulate each candidate INDEPENDENTLY
        evaluated_results = self._simulate_all_independent(
            candidates=all_plans,
            baseline_telemetry=canonical_telemetry,
            fault_diagnosis=fault_diagnosis,
        )

        return self._build_response(
            asset_id=asset_id,
            incident_id=incident_id,
            fault_diagnosis=fault_diagnosis,
            canonical_telemetry=canonical_telemetry,
            evaluated_results=evaluated_results,
        )

    # ------------------------------------------------------------------
    # Legacy API: evaluate_facility_state (used by /api/v1/counterfactual/evaluate)
    # ------------------------------------------------------------------

    def evaluate_facility_state(
        self,
        asset_id: str,
        current_telemetry: Dict[str, Any],
        fault_diagnosis: str = "nominal",
        incident_id: Optional[str] = None,
        sns_proposed_plan: Optional[Dict[str, Any]] = None,
    ) -> CounterfactualEvaluationResponse:
        """
        Legacy counterfactual evaluation path (direct evaluate endpoint).
        Used by /api/v1/counterfactual/evaluate.
        """
        canonical_telemetry = canonicalize_telemetry_dict(current_telemetry)

        candidates = CandidateGenerator.generate_candidates(
            fault_class=fault_diagnosis,
            current_telemetry=canonical_telemetry,
            sns_proposed_plan=sns_proposed_plan,
        )

        evaluated_results = self._simulate_all_independent(
            candidates=candidates,
            baseline_telemetry=canonical_telemetry,
            fault_diagnosis=fault_diagnosis,
        )

        return self._build_response(
            asset_id=asset_id,
            incident_id=incident_id,
            fault_diagnosis=fault_diagnosis,
            canonical_telemetry=canonical_telemetry,
            evaluated_results=evaluated_results,
        )

    # ------------------------------------------------------------------
    # Core simulation loop
    # ------------------------------------------------------------------

    def _simulate_all_independent(
        self,
        candidates: List[CandidatePlan],
        baseline_telemetry: Dict[str, float],
        fault_diagnosis: str,
    ) -> List[CounterfactualSimulationResult]:
        """
        Simulate every candidate starting from a FRESH COPY of baseline_telemetry.
        Candidate simulations are completely independent — no shared state.
        """
        evaluated_results: List[CounterfactualSimulationResult] = []

        for i, cand in enumerate(candidates):
            try:
                # CRITICAL: fresh copy for every branch — no mutation leakage
                branch_baseline = dict(baseline_telemetry)

                logger.debug(
                    f"[Engine] Simulating branch {i+1}/{len(candidates)}: "
                    f"{cand.candidate_id} interventions={cand.interventions}"
                )

                sim_out = self.simulator.simulate_candidate(
                    current_state=branch_baseline,
                    candidate=cand,
                )

                eval_res = CounterfactualEvaluator.evaluate(
                    current_state=dict(baseline_telemetry),  # fresh copy for evaluator too
                    candidate=cand,
                    sim_output=sim_out,
                    detected_fault=fault_diagnosis,
                )
                evaluated_results.append(eval_res)

                logger.debug(
                    f"[Engine] Branch {cand.candidate_id}: "
                    f"safety={'PASS' if not eval_res.violations else 'FAIL'} "
                    f"resolution={eval_res.resolution.status} "
                    f"status={eval_res.status}"
                )

            except Exception as e:
                logger.error(f"[Engine] Failed to evaluate candidate {cand.candidate_id}: {e}", exc_info=True)

        return evaluated_results

    # ------------------------------------------------------------------
    # Response builder
    # ------------------------------------------------------------------

    def _build_response(
        self,
        asset_id: str,
        incident_id: Optional[str],
        fault_diagnosis: str,
        canonical_telemetry: Dict[str, float],
        evaluated_results: List[CounterfactualSimulationResult],
    ) -> CounterfactualEvaluationResponse:
        """Rank candidates and build final response."""

        validated_candidates = [r for r in evaluated_results if r.status == ValidationStatus.VALIDATED]

        if validated_candidates:
            # Deterministic tie-breaker:
            # 1. Score (descending)
            # 2. Energy saved kW (descending)
            # 3. Minimal actuator disturbance (ascending)
            def tie_breaker(c: CounterfactualSimulationResult):
                movement = sum(
                    abs(c.proposed_interventions.get(act, canonical_telemetry.get(act, 0.0)) - canonical_telemetry.get(act, 0.0))
                    for act in c.proposed_interventions
                )
                return (c.score, c.energy_saved_kw, -movement)

            validated_candidates.sort(key=tie_breaker, reverse=True)
            winning_candidate = validated_candidates[0]
            overall_status = "VALIDATED"
            status_reason = (
                f"Candidate '{winning_candidate.candidate_id}' verified SAFE and "
                f"RESOLVES '{fault_diagnosis}' via Digital Twin simulation."
            )
        else:
            winning_candidate = None
            overall_status = "NO_VALIDATED_INTERVENTION"
            status_reason = (
                f"No candidate satisfied both SAFE and RESOLVES_ISSUE criteria for '{fault_diagnosis}'. "
                f"Evaluated {len(evaluated_results)} candidates. "
                f"Failure reasons: "
                + " | ".join([r.validation_summary for r in evaluated_results[:3]])
            )

        # Sort: VALIDATED first, NEEDS_REVIEW second, REJECTED last
        def sort_key(item: CounterfactualSimulationResult):
            status_priority = {
                ValidationStatus.VALIDATED: 3,
                ValidationStatus.NEEDS_REVIEW: 2,
                ValidationStatus.REJECTED: 1,
            }
            return (status_priority.get(item.status, 0), item.score)

        evaluated_results.sort(key=sort_key, reverse=True)

        n_safe = sum(1 for r in evaluated_results if not r.violations)
        n_resolves = sum(1 for r in evaluated_results if r.resolution.status.value == "RESOLVES_ISSUE")

        logger.info(
            f"[Engine] Result: evaluated={len(evaluated_results)} safe={n_safe} "
            f"resolves={n_resolves} validated={len(validated_candidates)} "
            f"status={overall_status}"
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
            status=overall_status,
            reason=status_reason,
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _merge_deduplicated(
        primary: List[CandidatePlan],
        secondary: List[CandidatePlan],
    ) -> List[CandidatePlan]:
        """Merge two candidate lists, deduplicating by intervention signature. Primary takes precedence."""
        seen: set = set()
        result: List[CandidatePlan] = []
        for cand in primary + secondary:
            sig = frozenset((k, round(v, 1)) for k, v in cand.interventions.items())
            if sig not in seen:
                seen.add(sig)
                result.append(cand)
        return result
