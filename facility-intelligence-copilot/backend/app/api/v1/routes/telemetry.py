from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, require_role
from app.db.session import get_db
from app.schemas.telemetry import TelemetryEvent
from app.services.digital_twin import DigitalTwinService
from app.services.telemetry_service import TelemetryService

router = APIRouter()

ASSET_LIBRARY = {
    1: {
        "id": 1,
        "asset_code": "HVAC-001",
        "name": "HVAC-001",
        "asset_type": "HVAC",
        "status": "healthy",
        "health_score": 94,
        "building_id": 1,
        "floor_id": 1,
    },
    2: {
        "id": 2,
        "asset_code": "HVAC-002",
        "name": "HVAC-002",
        "asset_type": "HVAC",
        "status": "healthy",
        "health_score": 91,
        "building_id": 1,
        "floor_id": 1,
    },
    3: {
        "id": 3,
        "asset_code": "HVAC-003",
        "name": "HVAC-003",
        "asset_type": "HVAC",
        "status": "warning",
        "health_score": 76,
        "building_id": 1,
        "floor_id": 2,
    },
    7: {
        "id": 7,
        "asset_code": "HVAC-007",
        "name": "HVAC-007",
        "asset_type": "HVAC",
        "status": "warning",
        "health_score": 68,
        "building_id": 1,
        "floor_id": 2,
    },
    8: {
        "id": 8,
        "asset_code": "CHILLER-001",
        "name": "CHILLER-001",
        "asset_type": "Chiller",
        "status": "healthy",
        "health_score": 89,
        "building_id": 1,
        "floor_id": 3,
    },
    9: {
        "id": 9,
        "asset_code": "CHILLER-002",
        "name": "CHILLER-002",
        "asset_type": "Chiller",
        "status": "healthy",
        "health_score": 93,
        "building_id": 1,
        "floor_id": 2,
    },
}

TELEMETRY_LIBRARY = {
    1: [
        {"event_id":"evt-101","event_type":"telemetry","asset_id":1,"timestamp":"2026-09-01T09:00:00Z","temperature":22.4,"pressure":3.6,"airflow":98.0,"energy_kw":5.2},
        {"event_id":"evt-102","event_type":"telemetry","asset_id":1,"timestamp":"2026-09-01T09:05:00Z","temperature":23.1,"pressure":3.8,"airflow":96.0,"energy_kw":5.5},
        {"event_id":"evt-103","event_type":"telemetry","asset_id":1,"timestamp":"2026-09-01T09:10:00Z","temperature":22.9,"pressure":3.7,"airflow":95.0,"energy_kw":5.4},
    ],
    7: [
        {"event_id":"evt-701","event_type":"telemetry","asset_id":7,"timestamp":"2026-09-01T12:00:00Z","temperature":28.9,"pressure":4.5,"airflow":72.0,"energy_kw":10.8},
        {"event_id":"evt-702","event_type":"telemetry","asset_id":7,"timestamp":"2026-09-01T12:05:00Z","temperature":29.4,"pressure":4.6,"airflow":70.0,"energy_kw":11.2},
        {"event_id":"evt-703","event_type":"telemetry","asset_id":7,"timestamp":"2026-09-01T12:10:00Z","temperature":29.7,"pressure":4.5,"airflow":68.0,"energy_kw":11.8},
        {"event_id":"evt-704","event_type":"telemetry","asset_id":7,"timestamp":"2026-09-01T12:15:00Z","temperature":30.1,"pressure":4.3,"airflow":64.0,"energy_kw":12.3},
    ],
    9: [
        {"event_id":"evt-901","event_type":"telemetry","asset_id":9,"timestamp":"2026-09-01T08:45:00Z","temperature":19.5,"pressure":6.2,"airflow":88.0,"energy_kw":8.0},
        {"event_id":"evt-902","event_type":"telemetry","asset_id":9,"timestamp":"2026-09-01T08:50:00Z","temperature":19.8,"pressure":6.3,"airflow":90.0,"energy_kw":8.3},
        {"event_id":"evt-903","event_type":"telemetry","asset_id":9,"timestamp":"2026-09-01T08:55:00Z","temperature":20.1,"pressure":6.1,"airflow":92.0,"energy_kw":8.5},
    ],
}

TWIN_LIBRARY = {
    1: {
        "asset_id": 1,
        "status": "healthy",
        "health_score": 94,
        "current_state": {"temperature": 23.1, "energy_kw": 5.5, "pressure": 3.8, "airflow": 96.0},
        "last_updated": "2026-09-01T09:05:00Z",
        "relationships": [
            {"type": "SERVES", "target": "Floor 1"},
            {"type": "MONITORED BY", "target": "TEMP-001"},
            {"type": "MONITORED BY", "target": "AIRFLOW-001"},
        ],
    },
    7: {
        "asset_id": 7,
        "status": "warning",
        "health_score": 68,
        "current_state": {"temperature": 30.1, "energy_kw": 12.3, "pressure": 4.3, "airflow": 64.0},
        "last_updated": "2026-09-01T12:15:00Z",
        "relationships": [
            {"type": "SERVES", "target": "Floor 2"},
            {"type": "DEPENDS ON", "target": "CHILLER-002"},
            {"type": "MONITORED BY", "target": "TEMP-007"},
            {"type": "MONITORED BY", "target": "ENERGY-007"},
            {"type": "MONITORED BY", "target": "PRESSURE-007"},
            {"type": "MONITORED BY", "target": "AIRFLOW-007"},
        ],
    },
    9: {
        "asset_id": 9,
        "status": "healthy",
        "health_score": 93,
        "current_state": {"temperature": 20.1, "energy_kw": 8.5, "pressure": 6.1, "airflow": 92.0},
        "last_updated": "2026-09-01T08:55:00Z",
        "relationships": [
            {"type": "SERVES", "target": "Floor 2"},
            {"type": "DEPENDS ON", "target": "CHILLER-001"},
            {"type": "MONITORED BY", "target": "TEMP-009"},
        ],
    },
}


def _readings_for_asset(asset_id: int) -> list[TelemetryEvent]:
    items = TELEMETRY_LIBRARY.get(asset_id, [])
    return [TelemetryEvent.model_validate(item) for item in items]


@router.post("/telemetry")
def ingest_telemetry(
    payload: TelemetryEvent,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role(["OPERATOR", "ADMIN"])),
):
    # 1. Update in-memory TELEMETRY_LIBRARY for instant dashboard chart updates
    if payload.asset_id not in TELEMETRY_LIBRARY:
        TELEMETRY_LIBRARY[payload.asset_id] = []

    event_dict = {
        "event_id": payload.event_id,
        "event_type": payload.event_type,
        "asset_id": payload.asset_id,
        "timestamp": payload.timestamp.isoformat().replace("+00:00", "Z") if hasattr(payload.timestamp, "isoformat") else str(payload.timestamp),
        "temperature": payload.temperature,
        "pressure": payload.pressure,
        "airflow": payload.airflow,
        "energy_kw": payload.energy_kw,
    }
    TELEMETRY_LIBRARY[payload.asset_id].append(event_dict)
    if len(TELEMETRY_LIBRARY[payload.asset_id]) > 100:
        TELEMETRY_LIBRARY[payload.asset_id] = TELEMETRY_LIBRARY[payload.asset_id][-100:]

    # 2. Update in-memory TWIN_LIBRARY snapshot
    if payload.asset_id in TWIN_LIBRARY:
        TWIN_LIBRARY[payload.asset_id]["current_state"] = {
            "temperature": payload.temperature,
            "energy_kw": payload.energy_kw,
            "pressure": payload.pressure,
            "airflow": payload.airflow,
        }
        TWIN_LIBRARY[payload.asset_id]["last_updated"] = event_dict["timestamp"]

    # 3. Process via TelemetryService for anomaly detection & alert generation
    try:
        service = TelemetryService(db)
        result = service.process_event(payload)
        return {
            "status": "accepted",
            "message": "Telemetry event validated and processed.",
            "event_id": payload.event_id,
            "asset_id": payload.asset_id,
            "asset_status": result.get("status"),
            "health_score": result.get("health_score"),
            "alerts": result.get("alerts", []),
        }
    except Exception:
        detected_anomalies = TelemetryService._detect_anomalies(payload)
        return {
            "status": "accepted",
            "message": "Telemetry event validated and accepted for processing.",
            "event_id": payload.event_id,
            "asset_id": payload.asset_id,
            "anomalies": detected_anomalies,
        }


@router.get("/assets/{asset_id}/telemetry")
def get_asset_telemetry(
    asset_id: int,
    limit: int = Query(25, ge=1, le=200),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
    user: AuthenticatedUser = Depends(require_role(["VIEWER"])),
):
    if asset_id not in ASSET_LIBRARY and asset_id not in TELEMETRY_LIBRARY:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    readings = _readings_for_asset(asset_id)
    if from_ is not None:
        readings = [item for item in readings if item.timestamp >= from_.astimezone(timezone.utc)]
    if to is not None:
        readings = [item for item in readings if item.timestamp <= to.astimezone(timezone.utc)]

    # Sort chronological and take the latest `limit` points
    sorted_all = sorted(readings, key=lambda item: item.timestamp)
    ordered = sorted_all[-limit:] if len(sorted_all) > limit else sorted_all
    return [
        {
            "timestamp": item.timestamp.isoformat().replace("+00:00", "Z"),
            "temperature": item.temperature,
            "energy_kw": item.energy_kw,
            "pressure": item.pressure,
            "airflow": item.airflow,
        }
        for item in ordered
    ]


@router.get("/twin/assets")
def get_twin_assets(user: AuthenticatedUser = Depends(require_role(["VIEWER"]))):
    return [
        {
            "asset_id": asset_id,
            **TWIN_LIBRARY[asset_id],
        }
        for asset_id in sorted(TWIN_LIBRARY)
    ]


@router.get("/twin/assets/{asset_id}")
def get_twin_asset(
    asset_id: int,
    user: AuthenticatedUser = Depends(require_role(["VIEWER"])),
):
    if asset_id not in TWIN_LIBRARY:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Digital twin asset not found")
    return TWIN_LIBRARY[asset_id]
