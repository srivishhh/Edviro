from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, HTTPException

from backend.counterfactual.engine import CounterfactualEngine
from backend.counterfactual.schemas import CounterfactualEvaluationResponse
from backend.app.services.digital_twin import DigitalTwinService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/counterfactual", tags=["counterfactual"])


@router.post("/evaluate", response_model=CounterfactualEvaluationResponse)
def evaluate_counterfactual(
    payload: Dict[str, Any] = Body(
        default={
            "asset_id": "AHU-007",
            "incident_id": None,
            "current_telemetry": None,
            "sns_proposed_plan": None,
        }
    )
) -> CounterfactualEvaluationResponse:
    """
    Executes real-time counterfactual state evaluation and constraint validation.
    Predicts thermodynamic response and energy savings across candidate intervention plans.
    """
    asset_id = payload.get("asset_id", "AHU-007")
    incident_id = payload.get("incident_id")
    current_telemetry = payload.get("current_telemetry")
    sns_proposed_plan = payload.get("sns_proposed_plan")

    twin_service = DigitalTwinService.get_instance()
    
    if current_telemetry:
        # User supplied explicit telemetry state
        cf_engine = CounterfactualEngine.get_instance()
        # Predict fault class
        fault_pred = twin_service.fault_predictor.predict(current_telemetry)
        fault_class = fault_pred.get("fault_class", "nominal")
        
        return cf_engine.evaluate_facility_state(
            asset_id=asset_id,
            current_telemetry=current_telemetry,
            fault_diagnosis=fault_class,
            incident_id=incident_id,
            sns_proposed_plan=sns_proposed_plan,
        )

    # Use current live digital twin state
    return twin_service.evaluate_counterfactual(
        asset_id=asset_id,
        incident_id=incident_id,
        sns_proposed_plan=sns_proposed_plan,
    )
