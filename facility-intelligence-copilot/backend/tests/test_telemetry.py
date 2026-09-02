from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.telemetry import TelemetryEvent
from app.services.digital_twin import DigitalTwinService


def test_telemetry_event_model_validates_sensor_fields():
    payload = {
        "event_id": "evt-001",
        "event_type": "telemetry",
        "asset_id": 42,
        "timestamp": "2025-09-01T12:00:00Z",
        "temperature": 74.2,
        "pressure": 101.2,
        "airflow": 120.0,
        "energy_kw": 8.4,
    }

    event = TelemetryEvent.model_validate(payload)

    assert event.event_id == "evt-001"
    assert event.asset_id == 42
    assert event.temperature == 74.2
    assert event.airflow == 120.0
    assert event.energy_kw == 8.4


@pytest.mark.parametrize(
    "payload",
    [
        {
            "event_id": "evt-002",
            "event_type": "telemetry",
            "asset_id": 0,
            "timestamp": "2025-09-01T12:00:00Z",
            "temperature": 72.0,
        },
        {
            "event_id": "evt-003",
            "event_type": "telemetry",
            "asset_id": 7,
            "timestamp": "2025-09-01T12:00:00Z",
            "temperature": -500,
        },
        {
            "event_id": "evt-004",
            "event_type": "telemetry",
            "asset_id": 7,
            "timestamp": "not-a-timestamp",
            "temperature": 72.0,
        },
    ],
)
def test_telemetry_event_rejects_invalid_payloads(payload):
    with pytest.raises(ValidationError):
        TelemetryEvent.model_validate(payload)


def test_digital_twin_service_tracks_anomalies_and_health():
    readings = [
        TelemetryEvent.model_validate({
            "event_id": "evt-101",
            "event_type": "telemetry",
            "asset_id": 7,
            "timestamp": "2025-09-01T12:00:00Z",
            "temperature": 82.0,
            "pressure": 100.7,
            "airflow": 45.0,
            "energy_kw": 7.9,
        }),
        TelemetryEvent.model_validate({
            "event_id": "evt-102",
            "event_type": "telemetry",
            "asset_id": 7,
            "timestamp": "2025-09-01T12:05:00Z",
            "temperature": 84.5,
            "pressure": 100.5,
            "airflow": 38.0,
            "energy_kw": 9.5,
        }),
    ]

    state = DigitalTwinService().build_snapshot(7, readings)

    assert state.asset_id == 7
    assert state.status in {"warning", "critical"}
    assert state.health_score < 100.0
    assert "airflow_restriction" in state.anomalies
