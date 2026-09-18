from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.v1.routes.replay import REPLAY_STATE
from app.services.lbnl_adapter import LBNLAdapter

router = APIRouter()
lbnl = LBNLAdapter()


async def event_generator():
    """Generates real-time Server-Sent Events (SSE) from the real LBNL dataset."""
    while True:
        is_playing = REPLAY_STATE.get("status") == "PLAYING"

        # Advance replay cursor ONLY if in PLAYING state
        if is_playing:
            step = max(1, int(REPLAY_STATE.get("speed_multiplier", 1.0)))
            REPLAY_STATE["current_row"] = (REPLAY_STATE.get("current_row", 1) + step) % REPLAY_STATE.get("total_rows", 525541)
            if REPLAY_STATE["current_row"] <= 0:
                REPLAY_STATE["current_row"] = 1

        curr_row = REPLAY_STATE.get("current_row", 421)
        reading = lbnl.get_reading(curr_row)

        # Synchronize live Digital Twin state with incoming telemetry frame
        from backend.app.services.digital_twin import DigitalTwinService
        twin_service = DigitalTwinService.get_instance()
        twin_state = twin_service.process_telemetry_frame(
            asset_id=reading.get("asset_id", "AHU-007"),
            raw_reading=reading,
        )

        data = {
            "type": "TELEMETRY_UPDATE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_dataset": "LBNL_AHU_annual.csv",
            "row_index": curr_row,
            "dataset_time": reading.get("dataset_timestamp"),
            "asset_id": reading.get("asset_id", "AHU-007"),
            "temperature": reading.get("temperature", 23.4),
            "temperature_f": reading.get("temperature_f", 74.1),
            "airflow": reading.get("airflow", 78.5),
            "airflow_cfm": reading.get("airflow_cfm", 7850),
            "pressure": reading.get("pressure", 3.8),
            "power": reading.get("power", 11.2),
            "damper_oa_pct": reading.get("damper_oa_pct", 30.0),
            "cooling_valve_pct": reading.get("cooling_valve_pct", 45.0),
            "facility_status": twin_state.status,
            "health_score": twin_state.health_score,
            "fault_diagnosis": twin_state.fault_diagnosis,
            "fault_probability": twin_state.fault_probability,
            "confidence": twin_state.confidence,
            "anomalies": twin_state.anomalies,
            "alert_id": reading.get("alert_id"),
            "alert_type": reading.get("alert_type"),
            "alert_title": reading.get("alert_title"),
            "severity": reading.get("severity"),
            "diagnosis": reading.get("diagnosis"),
            "prescription": reading.get("prescription"),
            "is_paused": not is_playing,
            "replay_status": REPLAY_STATE.get("status", "PLAYING"),
        }
        yield f"data: {json.dumps(data)}\n\n"
        await asyncio.sleep(1.5)  # Stream event every 1.5s


@router.get("/realtime/stream")
def realtime_stream():
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
