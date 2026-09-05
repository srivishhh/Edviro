from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.schemas.whatif import (
    WhatIfParameterState,
    WhatIfPreset,
    WhatIfSimulateRequest,
    WhatIfSimulateResponse,
)
from app.services.whatif_service import WhatIfSimulationService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/what-if/simulate", response_model=WhatIfSimulateResponse)
def run_what_if_simulation(payload: WhatIfSimulateRequest) -> WhatIfSimulateResponse:
    """
    Executes an isolated, read-only What-If decision support simulation.
    Takes an asset identifier and proposed parameter modifications,
    and returns predicted telemetry values, energy impact, health score,
    operational risk, explanation, and recommendations.
    
    GUARANTEES:
    - Zero write operations to database
    - Zero messages emitted to Kafka
    - Zero changes to Digital Twin
    - Zero real alarms or alerts generated
    """
    try:
        return WhatIfSimulationService.simulate(payload)
    except Exception as e:
        logger.error("Error executing What-If simulation for asset %s: %s", payload.asset_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"What-If simulation engine encountered an unexpected error: {str(e)}",
        )


@router.get("/what-if/presets", response_model=list[WhatIfPreset])
def get_simulation_presets() -> list[WhatIfPreset]:
    """
    Returns registered operational scenario presets (e.g. Normal Operation,
    Improve Airflow, Reduce Pressure, Energy Optimization, Stress Tests).
    """
    return WhatIfSimulationService.get_presets()


@router.get("/what-if/assets/{asset_id}/current")
def get_asset_current_simulation_state(asset_id: str) -> dict[str, Any]:
    """
    Retrieves the current operational telemetry and risk baseline for the target asset.
    Used by the What-If UI to pre-populate current slider positions.
    """
    code, name, state = WhatIfSimulationService.get_current_asset_state(asset_id)
    return {
        "asset_id": code,
        "asset_name": name,
        "current": state,
    }
