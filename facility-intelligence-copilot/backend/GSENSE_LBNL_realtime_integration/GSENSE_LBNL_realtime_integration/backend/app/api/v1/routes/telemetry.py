from datetime import datetime, timezone

from collections import defaultdict, deque

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.telemetry import TelemetryEvent
from app.services.digital_twin import DigitalTwinService
from app.services.telemetry_service import TelemetryService

router = APIRouter()

# Short live window used by the dashboard for replay/demo telemetry.
LIVE_TELEMETRY: dict[int, deque[dict]] = defaultdict(lambda: deque(maxlen=120))

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
def ingest_telemetry(payload: TelemetryEvent):
    """Process one live/replayed telemetry event and expose it to the dashboard."""
    try:
        result = TelemetryService().process_event(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    point = {
        "timestamp": payload.timestamp.isoformat().replace("+00:00", "Z"),
        "temperature": payload.temperature,
        "energy_kw": payload.energy_kw,
        "pressure": payload.pressure,
        "airflow": payload.airflow,
        "source": payload.source,
        "source_timestamp": payload.source_timestamp.isoformat() if payload.source_timestamp else None,
        "fault_ground_truth": payload.fault_ground_truth,
    }
    LIVE_TELEMETRY[payload.asset_id].append(point)
    return {"status": "processed", "event": point, **result}


@router.get("/assets/{asset_id}/telemetry")
def get_asset_telemetry(
    asset_id: int,
    limit: int = Query(25, ge=1, le=200),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
):
    if asset_id not in ASSET_LIBRARY:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    if LIVE_TELEMETRY.get(asset_id):
        points = list(LIVE_TELEMETRY[asset_id])
        if from_ is not None:
            points = [item for item in points if item["timestamp"] >= from_.astimezone(timezone.utc).isoformat()]
        if to is not None:
            points = [item for item in points if item["timestamp"] <= to.astimezone(timezone.utc).isoformat()]
        return points[-limit:]

    readings = _readings_for_asset(asset_id)
    if from_ is not None:
        readings = [item for item in readings if item.timestamp >= from_.astimezone(timezone.utc)]
    if to is not None:
        readings = [item for item in readings if item.timestamp <= to.astimezone(timezone.utc)]

    ordered = sorted(readings, key=lambda item: item.timestamp)[:limit]
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
def get_twin_assets():
    return [
        {
            "asset_id": asset_id,
            **TWIN_LIBRARY[asset_id],
        }
        for asset_id in sorted(TWIN_LIBRARY)
    ]


@router.get("/twin/assets/{asset_id}")
def get_twin_asset(asset_id: int):
    if asset_id not in TWIN_LIBRARY:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Digital twin asset not found")
    return TWIN_LIBRARY[asset_id]
