from datetime import datetime

from app.schemas.telemetry import TelemetryEvent
from app.services.telemetry_service import TelemetryService


def test_anomaly_detection_for_airflow_restriction():
    event = TelemetryEvent.model_validate({
        "event_id": "evt-200",
        "event_type": "telemetry",
        "asset_id": 7,
        "timestamp": "2026-09-01T12:00:00Z",
        "temperature": 30.0,
        "pressure": 4.6,
        "airflow": 72.0,
        "energy_kw": 12.0,
    })

    anomalies = TelemetryService._detect_anomalies(event)
    assert any(item["alert_type"] == "AIRFLOW_RESTRICTION" for item in anomalies)


def test_anomaly_detection_for_normal_event():
    event = TelemetryEvent.model_validate({
        "event_id": "evt-201",
        "event_type": "telemetry",
        "asset_id": 1,
        "timestamp": "2026-09-01T12:05:00Z",
        "temperature": 23.0,
        "pressure": 3.5,
        "airflow": 96.0,
        "energy_kw": 6.2,
    })

    anomalies = TelemetryService._detect_anomalies(event)
    assert anomalies == []
