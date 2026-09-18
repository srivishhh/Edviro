from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging
from fastapi import APIRouter, Body, HTTPException, status
from pydantic import BaseModel

from backend.ml.inference.state_predictor import StatePredictor
from backend.counterfactual.constraints import ConstraintChecker
from backend.counterfactual.resolution import ResolutionEvaluator, ResolutionStatus
from backend.counterfactual.engine import CounterfactualEngine
from backend.counterfactual.schemas import CandidatePlan
from backend.app.services.digital_twin import DigitalTwinService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["digital-twin"])


class SimulateCandidateRequest(BaseModel):
    incident_id: Optional[str] = None
    candidate: Dict[str, Any]
    baseline_state: Optional[Dict[str, Any]] = None
    detected_fault: Optional[str] = "nominal"


class SimulateAllRequest(BaseModel):
    incident_id: Optional[str] = None
    candidates: List[Dict[str, Any]]
    baseline_state: Optional[Dict[str, Any]] = None
    detected_fault: Optional[str] = "nominal"


@router.post("/api/digital-twin/simulate")
@router.post("/api/v1/digital-twin/simulate")
def simulate_single_candidate(payload: SimulateCandidateRequest) -> Dict[str, Any]:
    """
    SECTION 9: Counterfactual Single Candidate Simulation API.
    Evaluates one candidate action against an isolated copy of baseline state.
    """
    twin_service = DigitalTwinService.get_instance()
    
    # 1. Obtain baseline state
    baseline = payload.baseline_state
    if not baseline:
        cur_state = twin_service.get_state("AHU-007")
        baseline = cur_state.current_telemetry if cur_state else {
            "oa_temp": 24.0, "ra_temp": 23.0, "ma_temp": 23.5, "sa_temp": 14.5,
            "zone_temp": 22.8, "oa_dmpr": 25.0, "chwc_vlv": 35.0, "sf_spd": 70.0,
            "sa_cfm": 2500.0, "sa_sp": 1.5, "power": 8.5
        }

    cand = payload.candidate
    action_id = cand.get("action_id", "SNS-SIM-01")
    target = cand.get("target", "chwc_vlv")
    try:
        proposed_val = float(cand.get("proposed_value", 0.0))
    except (ValueError, TypeError):
        proposed_val = 0.0

    interventions = {target: proposed_val}

    # 2. Run isolated counterfactual prediction via StatePredictor
    state_predictor = StatePredictor.get_instance()
    sim_res = state_predictor.predict_counterfactual(
        current_state=baseline,
        interventions=interventions,
    )
    predicted_state = sim_res["predicted_state"]

    # 3. Evaluate safety constraints
    safety_status, violations, safety_score = ConstraintChecker.evaluate_constraints(
        current_state=baseline,
        interventions=interventions,
        predicted_state=predicted_state,
    )
    is_safe = len(violations) == 0

    # 4. Evaluate fault-specific resolution criteria
    fault_type = payload.detected_fault or "nominal"
    res_status, res_evidence = ResolutionEvaluator.evaluate_resolution(
        detected_fault=fault_type,
        baseline_state=baseline,
        predicted_state=predicted_state,
        is_safe=is_safe,
    )

    # 5. Formulaic Efficiency Calculations (SECTION 11)
    cur_power = float(baseline.get("power", 8.5))
    pred_power = float(predicted_state.get("power", cur_power))
    energy_delta_kw = round(cur_power - pred_power, 2)
    energy_change_pct = round(100.0 * energy_delta_kw / max(cur_power, 0.1), 1)

    cur_zone = float(baseline.get("zone_temp", 22.8))
    pred_zone = float(predicted_state.get("zone_temp", cur_zone))
    comfort_change = round(pred_zone - cur_zone, 2)

    cur_cfm = float(baseline.get("sa_cfm", 2500.0))
    pred_cfm = float(predicted_state.get("sa_cfm", cur_cfm))
    airflow_change = round(pred_cfm - cur_cfm, 1)

    efficiency_score = round(max(0.0, min(100.0, 70.0 + energy_change_pct * 0.5 - abs(comfort_change) * 5.0)), 1)

    provenance = {
        "telemetry": "KAFKA",
        "fault": "ML_MODEL",
        "candidate_generation": "SNS_LLM",
        "predicted_state": "DIGITAL_TWIN_STATE_MODEL",
        "resolution": "DETERMINISTIC_RESOLUTION_ENGINE",
        "efficiency": "DIGITAL_TWIN_METRICS",
    }

    return {
        "action_id": action_id,
        "status": "SIMULATED",
        "predicted_state": predicted_state,
        "resolution": {
            "resolved": res_status == ResolutionStatus.RESOLVES_ISSUE,
            "status": res_status.value,
            "resolution_margin": round(efficiency_score / 100.0, 3),
            "criteria": {
                "detected_fault": fault_type,
                "evidence": res_evidence,
            }
        },
        "efficiency": {
            "score": efficiency_score,
            "energy_change_kw": energy_delta_kw,
            "energy_change_pct": energy_change_pct,
            "comfort_change": comfort_change,
            "airflow_change": airflow_change,
        },
        "constraints": {
            "safe": is_safe,
            "violations": [v.model_dump() if hasattr(v, "model_dump") else str(v) for v in violations],
        },
        "provenance": provenance,
    }


@router.post("/api/digital-twin/simulate-all")
@router.post("/api/v1/digital-twin/simulate-all")
def simulate_all_candidates(payload: SimulateAllRequest) -> Dict[str, Any]:
    """
    SECTION 13 & 14: Sequential Simulation Endpoint (One at a time against identical baseline).
    """
    results: List[Dict[str, Any]] = []
    validated: List[Dict[str, Any]] = []

    for cand_raw in payload.candidates:
        sim_req = SimulateCandidateRequest(
            incident_id=payload.incident_id,
            candidate=cand_raw,
            baseline_state=payload.baseline_state,
            detected_fault=payload.detected_fault,
        )
        res = simulate_single_candidate(sim_req)
        results.append(res)
        if res["constraints"]["safe"] and res["resolution"]["resolved"]:
            validated.append(res)

    status_str = "VALIDATED" if len(validated) > 0 else "NO_VALIDATED_INTERVENTION"

    return {
        "incident_id": payload.incident_id,
        "simulations": results,
        "validated_interventions": validated,
        "status": status_str,
        "provenance": {
            "telemetry": "KAFKA",
            "fault": "ML_MODEL",
            "candidate_generation": "SNS_LLM",
            "predicted_state": "DIGITAL_TWIN_STATE_MODEL",
            "resolution": "DETERMINISTIC_RESOLUTION_ENGINE",
        },
    }


@router.post("/api/digital-twin/recommend")
@router.post("/api/v1/digital-twin/recommend")
def recommend_intervention(payload: SimulateAllRequest) -> Dict[str, Any]:
    """
    SECTION 21: Digital Twin Intervention Recommendation API.
    """
    sim_all_res = simulate_all_candidates(payload)
    validated = sim_all_res["validated_interventions"]

    if validated:
        # Sort by efficiency score descending
        validated.sort(key=lambda x: x["efficiency"]["score"], reverse=True)
        recommended = validated[0]
    else:
        recommended = None

    return {
        "incident_id": payload.incident_id,
        "recommended_intervention": recommended,
        "validated_count": len(validated),
        "total_evaluated": len(sim_all_res["simulations"]),
        "status": sim_all_res["status"],
        "provenance": sim_all_res["provenance"],
    }
