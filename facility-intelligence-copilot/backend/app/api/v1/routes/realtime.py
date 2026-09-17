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
        await asyncio.sleep(1.5)  # Stream event every 1.5s
        
        is_playing = REPLAY_STATE.get("status") == "PLAYING"

        # Advance replay cursor ONLY if in PLAYING state
        if is_playing:
            REPLAY_STATE["current_row"] = (REPLAY_STATE.get("current_row", 1) + 1) % REPLAY_STATE.get("total_rows", 525541)
            if REPLAY_STATE["current_row"] <= 0:
                REPLAY_STATE["current_row"] = 1

        curr_row = REPLAY_STATE.get("current_row", 421)
        reading = lbnl.get_reading(curr_row)

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
            "facility_status": reading.get("facility_status", "NORMAL"),
            "health_score": reading.get("health_score", 92),
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
