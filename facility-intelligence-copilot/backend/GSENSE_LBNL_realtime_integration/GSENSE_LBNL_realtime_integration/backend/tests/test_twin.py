from app.services.digital_twin import DigitalTwinService
from app.schemas.telemetry import TelemetryEvent


def test_twin_normal_state():
    readings = [
        TelemetryEvent.model_validate({
            "event_id": "evt-n1",
            "event_type": "telemetry",
            "asset_id": 1,
            "timestamp": "2026-09-01T12:00:00Z",
            "temperature": 23.0,
            "pressure": 3.6,
            "airflow": 96.0,
            "energy_kw": 5.5,
        })
    ]
    state = DigitalTwinService().build_snapshot(1, readings)
    assert state.status == "healthy"
    assert state.health_score == 100.0


def test_twin_warning_state():
    readings = [
        TelemetryEvent.model_validate({
            "event_id": "evt-w1",
            "event_type": "telemetry",
            "asset_id": 7,
            "timestamp": "2026-09-01T12:00:00Z",
            "temperature": 82.0,
            "pressure": 4.0,
            "airflow": 58.0,
            "energy_kw": 9.0,
        })
    ]
    state = DigitalTwinService().build_snapshot(7, readings)
    assert state.status in {"warning", "critical"}


def test_twin_critical_state():
    readings = [
        TelemetryEvent.model_validate({
            "event_id": "evt-c1",
            "event_type": "telemetry",
            "asset_id": 7,
            "timestamp": "2026-09-01T12:00:00Z",
            "temperature": 84.0,
            "pressure": 4.3,
            "airflow": 40.0,
            "energy_kw": 11.5,
        })
    ]
    state = DigitalTwinService().build_snapshot(7, readings)
    assert state.status == "critical"
