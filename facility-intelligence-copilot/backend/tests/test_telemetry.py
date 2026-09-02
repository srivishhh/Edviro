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


def test_telemetry_service_idempotent_processing():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.db.session import Base
    from app.models.facility import Asset, Sensor, SensorReading, Alert
    from app.services.telemetry_service import TelemetryService

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        asset = Asset(
            id=7,
            asset_code="HVAC-007",
            name="HVAC-007",
            asset_type="HVAC",
            status="healthy",
            health_score=100.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        sensor = Sensor(
            id=1,
            sensor_code="TEMP-007",
            asset_id=7,
            sensor_type="temperature",
            unit="°C",
            normal_min=18.0,
            normal_max=32.0,
            status="online",
            created_at=datetime.now(timezone.utc),
        )
        session.add(asset)
        session.add(sensor)
        session.commit()

        service = TelemetryService(db=session)
        event = TelemetryEvent.model_validate({
            "event_id": "evt-idem-001",
            "event_type": "telemetry",
            "asset_id": 7,
            "timestamp": "2026-09-01T12:00:00Z",
            "temperature": 29.5,
            "pressure": 3.8,
            "airflow": 70.0,
            "energy_kw": 11.0,
        })

        # Process first time
        result1 = service.process_event(event)
        readings_count_1 = session.query(SensorReading).count()
        assert readings_count_1 == 1

        # Process same event_id second time (should be idempotent)
        result2 = service.process_event(event)
        readings_count_2 = session.query(SensorReading).count()
        assert readings_count_2 == 1
        assert result2.get("idempotent_skip") is True


def test_telemetry_service_alert_recovery():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.db.session import Base
    from app.models.facility import Asset, Sensor, SensorReading, Alert
    from app.services.telemetry_service import TelemetryService

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        asset = Asset(
            id=7,
            asset_code="HVAC-007",
            name="HVAC-007",
            asset_type="HVAC",
            status="healthy",
            health_score=100.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        sensor = Sensor(
            id=1,
            sensor_code="TEMP-007",
            asset_id=7,
            sensor_type="temperature",
            unit="°C",
            normal_min=18.0,
            normal_max=32.0,
            status="online",
            created_at=datetime.now(timezone.utc),
        )
        session.add(asset)
        session.add(sensor)
        session.commit()

        service = TelemetryService(db=session)

        # 1. Fault occurs: airflow restriction
        fault_event = TelemetryEvent.model_validate({
            "event_id": "evt-fault-001",
            "event_type": "telemetry",
            "asset_id": 7,
            "timestamp": "2026-09-01T12:00:00Z",
            "temperature": 29.5,
            "pressure": 4.5,
            "airflow": 60.0,
            "energy_kw": 11.5,
        })
        fault_res = service.process_event(fault_event)
        assert fault_res["status"] in {"warning", "critical"}
        assert len(fault_res["alerts"]) > 0

        # Check alert is open in DB
        open_alerts = session.query(Alert).filter(Alert.asset_id == 7, Alert.status == "OPEN").all()
        assert len(open_alerts) > 0

        # 2. Recovery occurs: normal telemetry
        normal_event = TelemetryEvent.model_validate({
            "event_id": "evt-normal-001",
            "event_type": "telemetry",
            "asset_id": 7,
            "timestamp": "2026-09-01T12:10:00Z",
            "temperature": 22.0,
            "pressure": 3.5,
            "airflow": 95.0,
            "energy_kw": 5.5,
        })
        norm_res = service.process_event(normal_event)
        assert norm_res["status"] == "healthy"
        assert norm_res["health_score"] == 100.0

        # Alert should now be RESOLVED, not deleted
        resolved_alerts = session.query(Alert).filter(Alert.asset_id == 7, Alert.status == "RESOLVED").all()
        assert len(resolved_alerts) > 0
        total_alerts = session.query(Alert).filter(Alert.asset_id == 7).count()
        assert total_alerts > 0  # History preserved

