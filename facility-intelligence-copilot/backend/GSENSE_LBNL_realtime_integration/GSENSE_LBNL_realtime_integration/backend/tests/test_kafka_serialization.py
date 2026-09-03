import json

from app.schemas.telemetry import TelemetryEvent


def test_kafka_telemetry_serialization_round_trip():
    payload = {
        "event_id": "evt-kafka-1",
        "event_type": "telemetry",
        "asset_id": 7,
        "timestamp": "2026-09-01T12:00:00Z",
        "temperature": 28.5,
        "pressure": 4.2,
        "airflow": 78.0,
        "energy_kw": 10.1,
    }

    event = TelemetryEvent.model_validate(payload)
    serialized = json.dumps(event.model_dump(mode="json"))
    deserialized = TelemetryEvent.model_validate(json.loads(serialized))

    assert deserialized.asset_id == 7
    assert deserialized.temperature == 28.5
    assert deserialized.airflow == 78.0
