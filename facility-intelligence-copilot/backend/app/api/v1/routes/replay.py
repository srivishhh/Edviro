from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.lbnl_adapter import LBNLAdapter

router = APIRouter()
lbnl = LBNLAdapter()

# Replay Engine state
REPLAY_STATE: Dict = {
    "status": "PLAYING",  # PLAYING, PAUSED, RESTARTING
    "current_row": 421,
    "total_rows": lbnl.total_rows,
    "source_time": "09:41:32",
    "dataset": "LBNL_AHU_annual.csv",
    "speed_multiplier": 1.0,
    "last_updated": datetime.now(timezone.utc).isoformat(),
}


class ReplayControlRequest(BaseModel):
    action: str  # play, pause, rewind, restart


@router.get("/replay/state")
def get_replay_state():
    if REPLAY_STATE["status"] == "PLAYING":
        REPLAY_STATE["current_row"] += 1
        if REPLAY_STATE["current_row"] > REPLAY_STATE["total_rows"]:
            REPLAY_STATE["current_row"] = 1
    REPLAY_STATE["total_rows"] = lbnl.total_rows
    reading = lbnl.get_reading(REPLAY_STATE["current_row"])
    REPLAY_STATE["source_time"] = reading.get("dataset_timestamp", "2018-01-01 09:41:32")
    REPLAY_STATE["last_updated"] = datetime.now(timezone.utc).isoformat()
    return REPLAY_STATE


@router.post("/replay/control")
def control_replay(payload: ReplayControlRequest):
    action = payload.action.lower()
    now_str = datetime.now(timezone.utc).isoformat()

    if action == "play":
        REPLAY_STATE["status"] = "PLAYING"
    elif action == "pause":
        REPLAY_STATE["status"] = "PAUSED"
    elif action == "rewind":
        REPLAY_STATE["current_row"] = max(1, REPLAY_STATE["current_row"] - 100)
        REPLAY_STATE["status"] = "PLAYING"
    elif action == "restart":
        REPLAY_STATE["current_row"] = 1
        REPLAY_STATE["status"] = "PLAYING"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid replay action: {payload.action}. Use play, pause, rewind, restart."
        )

    REPLAY_STATE["last_updated"] = now_str
    return {
        "message": f"Replay engine executed action: {action.upper()}",
        "state": REPLAY_STATE,
    }
