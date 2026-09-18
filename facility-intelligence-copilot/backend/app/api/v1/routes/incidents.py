from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, HTTPException

from backend.app.services.digital_twin import DigitalTwinService
from backend.counterfactual.engine import CounterfactualEngine
from backend.counterfactual.schemas import CounterfactualEvaluationResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incidents", tags=["incidents"])

# In-memory incident tracking store
_active_incident_store: Dict[str, Dict[str, Any]] = {}
_actuation_history: List[Dict[str, Any]] = []


@router.get("/active")
def get_active_incident() -> Dict[str, Any]:
    """
    Returns current active facility incident diagnosed from telemetry and ML fault models.
    """
    twin_service = DigitalTwinService.get_instance()
    state = twin_service.get_state("AHU-007")

    if not state:
        from backend.app.api.v1.routes.replay import REPLAY_STATE
        from backend.app.services.lbnl_adapter import LBNLAdapter
        lbnl = LBNLAdapter()
        reading = lbnl.get_reading(REPLAY_STATE.get("current_row", 1))
        state = twin_service.process_telemetry_frame("AHU-007", reading)

    fault_diagnosis = getattr(state, "fault_diagnosis", "nominal") or "nominal"
    health_score = float(getattr(state, "health_score", 100.0) or 100.0)
    is_anomalous = fault_diagnosis != "nominal" or health_score < 75.0
    incident_id = f"INC-{fault_diagnosis.upper().replace('_', '-')}-001" if is_anomalous else None
    
    # Run counterfactual analysis
    cf_res = twin_service.evaluate_counterfactual(
        asset_id="AHU-007",
        incident_id=incident_id,
    )

    return {
        "has_active_incident": is_anomalous,
        "incident_id": incident_id,
        "asset_id": state.asset_id,
        "asset_name": state.asset_name,
        "facility_status": state.status,
        "health_score": state.health_score,
        "fault_diagnosis": state.fault_diagnosis,
        "fault_probability": state.fault_probability,
        "confidence": state.confidence,
        "indicators": state.anomalies,
        "current_telemetry": state.current_telemetry,
        "counterfactual_solution": cf_res.model_dump(),
        "last_updated": state.last_updated,
    }


@router.post("/actuate")
def apply_actuation(
    payload: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """
    Technician Human-in-the-Loop actuation approval endpoint.
    Applies validated intervention parameters to the Digital Twin and logs audit provenance.
    """
    candidate_id = payload.get("candidate_id")
    interventions = payload.get("interventions", {})
    operator_notes = payload.get("notes", "Approved via GSENSE 3.0 Technician UI")
    asset_id = payload.get("asset_id", "AHU-007")

    if not interventions:
        raise HTTPException(status_code=400, detail="No interventions provided in payload.")

    twin_service = DigitalTwinService.get_instance()
    cur_state = twin_service.get_state(asset_id)
    
    cur_telemetry = cur_state.current_telemetry if cur_state else {}
    updated_telemetry = dict(cur_telemetry)
    for k, v in interventions.items():
        updated_telemetry[k] = float(v)

    # Re-evaluate twin under new actuated state
    new_twin_state = twin_service.process_telemetry_frame(asset_id, updated_telemetry)

    actuation_record = {
        "actuation_id": f"ACT-{len(_actuation_history) + 1:04d}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset_id": asset_id,
        "candidate_id": candidate_id,
        "interventions": interventions,
        "operator_notes": operator_notes,
        "post_actuation_health_score": new_twin_state.health_score,
        "post_actuation_status": new_twin_state.status,
    }
    _actuation_history.append(actuation_record)

    return {
        "success": True,
        "message": f"Intervention successfully actuated on {asset_id}.",
        "actuation_record": actuation_record,
        "updated_twin_state": {
            "health_score": new_twin_state.health_score,
            "status": new_twin_state.status,
            "fault_diagnosis": new_twin_state.fault_diagnosis,
        }
    }


@router.post("/{incident_id}/investigate")
def investigate_incident(
    incident_id: str,
    payload: Optional[Dict[str, Any]] = Body(default=None)
) -> Dict[str, Any]:
    """
    Executes complete GSENSE 3.0 workflow:
    Incident -> SNS Workbench (3.0 GSense) -> 6-8 Independent Candidate Actions
    -> Digital Twin Virtual Simulations (one branch per candidate, independent baseline)
    -> Safety & Resolution Verification -> Validated Technician Output

    CRITICAL: Each SNS candidate_action is simulated as an INDEPENDENT Digital Twin branch.
    No merging of candidate actions occurs before simulation.
    """
    from backend.app.integrations.sns_workbench import SNSWorkbenchClient

    payload = payload or {}
    asset_id = payload.get("asset_id", "AHU-007")
    twin_service = DigitalTwinService.get_instance()
    state = twin_service.get_state(asset_id)

    if not state:
        raw = {
            "oa_temp": 32.5, "ra_temp": 24.2, "ma_temp": 29.8, "sa_temp": 21.0,
            "zone_temp": 25.8, "oa_dmpr": 85.0, "chwc_vlv": 95.0, "sf_spd": 80.0,
            "sa_cfm": 2450.0, "sa_sp": 1.6, "power": 14.2
        }
        state = twin_service.process_telemetry_frame(asset_id, raw)

    detected_fault = payload.get("detected_fault", state.fault_diagnosis)
    fault_confidence = float(getattr(state, "fault_probability", 0.0) or payload.get("fault_confidence", 0.0))
    current_telemetry = payload.get("current_telemetry", state.current_telemetry)
    anomaly_evidence = list(getattr(state, "anomalies", []) or [])

    # 1. Execute SNS 3.0 Workbench — receives complete incident context
    sns_client = SNSWorkbenchClient()
    sns_result = sns_client.generate_fault_candidates(
        incident_id=incident_id,
        asset_id=asset_id,
        detected_fault=detected_fault,
        fault_confidence=fault_confidence,
        anomaly_evidence=anomaly_evidence,
        current_state=current_telemetry,
        actuators={
            "oa_dmpr": float(current_telemetry.get("oa_dmpr", 25.0)),
            "chwc_vlv": float(current_telemetry.get("chwc_vlv", 35.0)),
            "sf_spd": float(current_telemetry.get("sf_spd", 70.0)),
            "hw_vlv": float(current_telemetry.get("hw_vlv", 0.0)),
        },
        available_controls=["oa_dmpr", "chwc_vlv", "sf_spd", "hw_vlv"],
    )

    # 2. Collect SNS candidate_actions list — DO NOT MERGE into one dict
    sns_candidate_actions = sns_result.get("candidate_actions", [])

    logger.info(
        f"[Investigate] incident={incident_id} fault={detected_fault} "
        f"sns_candidates={len(sns_candidate_actions)}"
    )

    # 3. Simulate EACH candidate independently in the Digital Twin
    cf_engine = CounterfactualEngine.get_instance()
    evaluation_res = cf_engine.evaluate_with_sns_candidates(
        asset_id=asset_id,
        current_telemetry=current_telemetry,
        fault_diagnosis=detected_fault,
        sns_candidate_actions=sns_candidate_actions,
        incident_id=incident_id,
    )

    # 4. Round 2 Fallback Protocol (max 2 rounds) if 0 candidates are validated
    round_number = 1
    if not evaluation_res.winning_candidate and evaluation_res.all_candidates:
        round_number = 2
        logger.info(f"[Investigate] Round 1 produced 0 validated interventions. Triggering Round 2 re-evaluation...")
        failed_cands = [c.model_dump() for c in evaluation_res.all_candidates]
        failure_reasons = [c.validation_summary for c in evaluation_res.all_candidates]

        sns_result_r2 = sns_client.generate_fault_candidates(
            incident_id=incident_id,
            asset_id=asset_id,
            detected_fault=detected_fault,
            fault_confidence=fault_confidence,
            anomaly_evidence=anomaly_evidence,
            current_state=current_telemetry,
            actuators={
                "oa_dmpr": float(current_telemetry.get("oa_dmpr", 25.0)),
                "chwc_vlv": float(current_telemetry.get("chwc_vlv", 35.0)),
                "sf_spd": float(current_telemetry.get("sf_spd", 70.0)),
                "hw_vlv": float(current_telemetry.get("hw_vlv", 0.0)),
            },
            available_controls=["oa_dmpr", "chwc_vlv", "sf_spd", "hw_vlv"],
            round_number=2,
            failed_candidates=failed_cands,
            simulation_failure_reasons=failure_reasons,
        )

        r2_candidate_actions = sns_result_r2.get("candidate_actions", [])
        if r2_candidate_actions:
            sns_candidate_actions.extend(r2_candidate_actions)
            evaluation_res = cf_engine.evaluate_with_sns_candidates(
                asset_id=asset_id,
                current_telemetry=current_telemetry,
                fault_diagnosis=detected_fault,
                sns_candidate_actions=r2_candidate_actions,
                incident_id=incident_id,
            )
            sns_result = sns_result_r2

    n_safe = sum(1 for c in evaluation_res.all_candidates if not c.violations)
    n_resolves = sum(1 for c in evaluation_res.all_candidates if c.resolution.status.value == "RESOLVES_ISSUE")
    n_validated = sum(1 for c in evaluation_res.all_candidates if c.status.value == "VALIDATED")

    provenance = {
        "telemetry_source": "KAFKA_LBNL_STREAM",
        "anomaly_detector": "fault_classifier.joblib (HistGradientBoostingClassifier)",
        "candidate_generator": f"SNS Workbench 3.2 (OpenRouter LLM) - Round {round_number}",
        "digital_twin_surrogate": "state_regressors.joblib (HistGradientBoostingRegressor)",
        "resolution_evaluator": "Deterministic Physics & ASHRAE Constraint Engine",
    }

    return {
        "incident_id": incident_id,
        "detected_fault": detected_fault,
        "fault_confidence": fault_confidence,
        "round_number": round_number,
        "sns": {
            "workflow_name": sns_result.get("workflow_name", "3.0 GSense"),
            "workflow_id": sns_result.get("workflow_id"),
            "execution_id": sns_result.get("execution_id"),
            "status": sns_result.get("status", "COMPLETED"),
            "candidates_generated": len(sns_candidate_actions),
            "candidate_actions": sns_candidate_actions,
            "diagnosis": sns_result.get("diagnosis", {}),
        },
        "simulation_summary": {
            "total_simulated": len(evaluation_res.all_candidates),
            "safe": n_safe,
            "resolves": n_resolves,
            "validated": n_validated,
        },
        "provenance": provenance,
        "simulations": [c.model_dump() for c in evaluation_res.all_candidates],
        "validated_intervention": evaluation_res.winning_candidate.model_dump() if evaluation_res.winning_candidate else None,
        "status": evaluation_res.status,
        "reason": evaluation_res.reason,
    }


@router.get("/actuation/history")
def get_actuation_history() -> List[Dict[str, Any]]:
    return _actuation_history

