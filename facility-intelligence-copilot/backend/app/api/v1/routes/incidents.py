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


@router.get("/actuation/history")
def get_actuation_history() -> List[Dict[str, Any]]:
    return _actuation_history
