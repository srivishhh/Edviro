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
        # Generate initial state
        raw = {
            "oa_temp": 32.5, "ra_temp": 24.2, "ma_temp": 29.8, "sa_temp": 21.0,
            "zone_temp": 25.8, "oa_dmpr": 85.0, "chwc_vlv": 95.0, "sf_spd": 80.0,
            "sa_cfm": 2450.0, "sa_sp": 1.6, "power": 14.2
        }
        state = twin_service.process_telemetry_frame("AHU-007", raw)

    is_anomalous = state.fault_diagnosis != "nominal" or state.health_score < 75.0

    incident_id = "INC-3001" if is_anomalous else None
    
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
    Incident -> SNS Workbench (3.0 GSense) -> Candidate Actions -> Digital Twin Virtual Simulations -> Safety & Resolution Verification -> Validated Technician Output
    """
    from app.integrations.sns_workbench import SNSWorkbenchClient

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
    current_telemetry = payload.get("current_telemetry", state.current_telemetry)

    # 1. Execute SNS 3.0 Workbench workflow
    sns_client = SNSWorkbenchClient()
    sns_result = sns_client.generate_fault_candidates(
        incident_id=incident_id,
        asset_id=asset_id,
        detected_fault=detected_fault,
        current_state=current_telemetry,
        actuators={
            "oa_dmpr": current_telemetry.get("oa_dmpr", 25.0),
            "chwc_vlv": current_telemetry.get("chwc_vlv", 35.0),
            "sf_spd": current_telemetry.get("sf_spd", 70.0),
            "hw_vlv": current_telemetry.get("hw_vlv", 0.0),
        },
    )

    # 2. Package SNS candidate into simulation engine
    cf_engine = CounterfactualEngine.get_instance()
    candidate_actions_list = sns_result.get("candidate_actions", [])
    primary_candidate_action = candidate_actions_list[0] if candidate_actions_list else {}
    sns_proposed = {
        "title": f"SNS 3.0 Proposed Action ({primary_candidate_action.get('target', 'Actuator')})",
        "description": primary_candidate_action.get("reason", "SNS 3.0 AI Candidate"),
        "interventions": {
            a["target"]: a["proposed_value"]
            for a in candidate_actions_list
            if "target" in a and "proposed_value" in a
        },
        "rationale": primary_candidate_action.get("reason", "Cognitive candidate from 3.0 GSense workflow"),
    }

    # 3. Simulate and Validate in Digital Twin
    evaluation_res = cf_engine.evaluate_facility_state(
        asset_id=asset_id,
        current_telemetry=current_telemetry,
        fault_diagnosis=detected_fault,
        incident_id=incident_id,
        sns_proposed_plan=sns_proposed,
    )

    return {
        "incident_id": incident_id,
        "detected_fault": detected_fault,
        "sns": {
            "workflow_name": sns_result.get("workflow_name", "3.0 GSense"),
            "workflow_id": sns_result.get("workflow_id"),
            "execution_id": sns_result.get("execution_id"),
            "status": sns_result.get("status", "COMPLETED"),
            "candidate_count": len(candidate_actions_list),
            "candidate_actions": candidate_actions_list,
        },
        "simulations": [c.model_dump() for c in evaluation_res.all_candidates],
        "validated_intervention": evaluation_res.winning_candidate.model_dump() if evaluation_res.winning_candidate else None,
        "status": evaluation_res.status,
        "reason": evaluation_res.reason,
    }


@router.get("/actuation/history")
def get_actuation_history() -> List[Dict[str, Any]]:
    return _actuation_history

