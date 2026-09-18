from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional
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
    action: str  # play, pause, rewind, forward, fast_forward, restart, seek
    target_row: Optional[int] = None
    step_size: Optional[int] = 500
    speed: Optional[float] = None


def _sync_reading_to_digital_twin(reading: Dict) -> None:
    """Syncs live LBNL replay slider position and anomaly profile directly to DigitalTwinService."""
    from backend.app.services.digital_twin import DigitalTwinService

    sat = float(reading.get("temperature", 21.0))
    mat = float(reading.get("mixed_air_temp", 29.8))
    oat = float(reading.get("outdoor_air_temp", 32.5))
    rat = float(reading.get("return_air_temp", 24.2))
    cfm = float(reading.get("airflow_cfm", 2450.0))
    sp = float(reading.get("pressure", 1.6))
    pwr = float(reading.get("power", 14.2))
    oad = float(reading.get("damper_oa_pct", 85.0))
    chwc = float(reading.get("cooling_valve_pct", 95.0))

    raw_telemetry = {
        "oa_temp": oat,
        "ra_temp": rat,
        "ma_temp": mat,
        "sa_temp": sat,
        "zone_temp": round(rat + 1.0, 1),
        "oa_dmpr": oad,
        "chwc_vlv": chwc,
        "sf_spd": round(max(20.0, min(100.0, cfm / 35.0)), 1),
        "sa_cfm": cfm,
        "sa_sp": sp,
        "power": pwr,
    }

    twin_service = DigitalTwinService.get_instance()
    state = twin_service.process_telemetry_frame("AHU-007", raw_telemetry)

    # Align fault diagnosis with active LBNL anomaly profile
    alert_type = reading.get("alert_type", "NOMINAL_OPERATION")
    alert_map = {
        "AIRFLOW_RESTRICTION": "fan_belt_slip",
        "COOLING_COIL_FOULING": "coi_stuck",
        "STATIC_PRESSURE_SURGE": "static_pressure_surge",
        "ECONOMIZER_LEAKAGE": "damper_stuck",
        "NOMINAL_OPERATION": "nominal",
    }
    mapped_fault = alert_map.get(alert_type, "nominal")

    state.fault_diagnosis = mapped_fault
    if mapped_fault != "nominal":
        state.status = reading.get("facility_status", "DEGRADED")
        state.health_score = float(reading.get("health_score", 60.0))
        state.anomalies = [reading.get("diagnosis", f"LBNL anomaly: {alert_type}")]
        state.fault_probability = 0.92
    else:
        state.status = "NOMINAL"
        state.health_score = 95.0
        state.anomalies = []
        state.fault_probability = 0.0


@router.get("/replay/state")
def get_replay_state():
    if REPLAY_STATE["status"] == "PLAYING":
        step = int(REPLAY_STATE.get("speed_multiplier", 1.0) * 1)
        REPLAY_STATE["current_row"] += step
        if REPLAY_STATE["current_row"] > REPLAY_STATE["total_rows"]:
            REPLAY_STATE["current_row"] = 1
    REPLAY_STATE["total_rows"] = lbnl.total_rows
    reading = lbnl.get_reading(REPLAY_STATE["current_row"])

    # Sync live reading to Digital Twin
    _sync_reading_to_digital_twin(reading)

    REPLAY_STATE["source_time"] = reading.get("dataset_timestamp", "2018-01-01 09:41:32")
    REPLAY_STATE["active_anomaly"] = {
        "alert_id": reading.get("alert_id"),
        "alert_type": reading.get("alert_type"),
        "alert_title": reading.get("alert_title"),
        "severity": reading.get("severity"),
        "facility_status": reading.get("facility_status"),
        "health_score": reading.get("health_score"),
        "diagnosis": reading.get("diagnosis"),
        "prescription": reading.get("prescription"),
    }
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
        step = payload.step_size or 500
        REPLAY_STATE["current_row"] = max(1, REPLAY_STATE["current_row"] - step)
    elif action == "forward" or action == "fast_forward":
        step = payload.step_size or 500
        REPLAY_STATE["current_row"] = min(REPLAY_STATE["total_rows"], REPLAY_STATE["current_row"] + step)
    elif action == "restart":
        REPLAY_STATE["current_row"] = 1
        REPLAY_STATE["status"] = "PLAYING"
    elif action == "seek":
        if payload.target_row is not None:
            clamped = max(1, min(REPLAY_STATE["total_rows"], payload.target_row))
            REPLAY_STATE["current_row"] = clamped
    elif action == "speed":
        if payload.speed is not None and payload.speed > 0:
            REPLAY_STATE["speed_multiplier"] = float(payload.speed)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid replay action: {payload.action}. Use play, pause, rewind, forward, restart, seek, speed."
        )

    reading = lbnl.get_reading(REPLAY_STATE["current_row"])

    # Sync live reading to Digital Twin
    _sync_reading_to_digital_twin(reading)

    REPLAY_STATE["source_time"] = reading.get("dataset_timestamp", "2018-01-01 09:41:32")
    REPLAY_STATE["active_anomaly"] = {
        "alert_id": reading.get("alert_id"),
        "alert_type": reading.get("alert_type"),
        "alert_title": reading.get("alert_title"),
        "severity": reading.get("severity"),
        "facility_status": reading.get("facility_status"),
        "health_score": reading.get("health_score"),
        "diagnosis": reading.get("diagnosis"),
        "prescription": reading.get("prescription"),
    }
    REPLAY_STATE["last_updated"] = now_str
    return {
        "message": f"Replay engine executed action: {action.upper()}",
        "state": REPLAY_STATE,
    }
