import csv
from datetime import datetime, timezone
from pathlib import Path
from fastapi.testclient import TestClient

from main import app
from app.schemas.telemetry import TelemetryEvent
from app.services.telemetry_service import TelemetryService
from app.xray.service import XRayService
from scripts.replay_lbnl_rtu import (
    find_csv_path,
    transform_lbnl_row,
    fahrenheit_to_celsius,
    psi_to_bar,
)

client = TestClient(app)


def test_lbnl_csv_file_exists_and_parseable():
    csv_path = find_csv_path()
    assert csv_path.is_file()
    assert csv_path.stat().st_size > 10000

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert "Timestamp" in headers
        assert "RTU: Supply Air Temperature" in headers
        assert "RTU: Circuit 1 Discharge Pressure" in headers
        assert "RTU: Supply Air Volumetric Flow Rate" in headers
        assert "RTU: Electricity" in headers
        assert len(headers) >= 60


def test_lbnl_unit_conversions():
    assert abs(fahrenheit_to_celsius(32.0) - 0.0) < 0.01
    assert abs(fahrenheit_to_celsius(212.0) - 100.0) < 0.01
    assert round(fahrenheit_to_celsius(68.0), 2) == 20.0
    assert round(psi_to_bar(456.6), 2) == 31.48


def test_lbnl_row_transformation():
    sample_row = {
        "Timestamp": "8/27/2017 6:44",
        "RTU: Supply Air Temperature": "61.0",
        "RTU: Return Air Temperature": "73.5",
        "RTU: Circuit 1 Condenser Outlet Temperature": "106.3",
        "RTU: Circuit 1 Discharge Pressure": "456.6",
        "RTU: Supply Air Volumetric Flow Rate": "4392",
        "RTU: Electricity": "140.58",
        "RTU: Supply Air Fan Status": "1",
        "RTU: Compressor 1 On/Off Status": "1",
        "Occupancy Mode Indicator": "1",
    }

    event = transform_lbnl_row(sample_row, row_idx=405, asset_id=7)
    assert event["asset_id"] == 7
    assert event["temperature"] == round(fahrenheit_to_celsius(61.0), 2)
    assert event["pressure"] == round(psi_to_bar(456.6), 2)
    assert event["energy_kw"] == 140.58
    assert event["airflow"] == round((4392 / 4500.0) * 100.0, 1)
    assert event["raw_data"]["source"] == "LBNL_RTU_HISTORICAL_REPLAY"
    assert event["raw_data"]["discharge_pressure_psi"] == 456.6

    telemetry_obj = TelemetryEvent.model_validate(event)
    assert telemetry_obj.pressure > 30.0


def test_condenser_fouling_anomaly_detection():
    fouling_event = TelemetryEvent(
        event_id="evt-fouling-001",
        event_type="telemetry",
        asset_id=7,
        timestamp=datetime.now(timezone.utc),
        temperature=22.0,
        pressure=31.5,
        airflow=95.0,
        energy_kw=140.5,
        raw_data={"condenser_temp_c": 41.3},
    )

    anomalies = TelemetryService._detect_anomalies(fouling_event)
    alert_types = [a["alert_type"] for a in anomalies]
    assert "CONDENSER_FOULING" in alert_types

    fouling_alert = next(a for a in anomalies if a["alert_type"] == "CONDENSER_FOULING")
    assert fouling_alert["anomaly_score"] >= 0.80
    assert "Condenser fouling pattern detected" in fouling_alert["message"]
    assert fouling_alert["severity"] in ["HIGH", "WARNING"]


def test_xray_condenser_fouling_causal_reasoning():
    service = XRayService()
    
    class MockContext:
        alert = {"alert_type": "CONDENSER_FOULING", "severity": "HIGH"}
        asset = {"id": 7, "asset_code": "HVAC-007"}
        current_state = {"temperature": 22.0, "pressure": 31.5, "energy_kw": 140.5, "airflow": 95.0}
        evidence = []
        relationships = []
        anomaly = {"description": "Elevated discharge pressure"}

    observed, inferred, alternative_causes, recommended_actions, root_cause, confidence = service._derive_reasoning(MockContext())

    assert any("Compressor discharge head pressure" in o for o in observed)
    assert any("heat transfer resistance" in i for i in inferred)
    assert "Condenser coil fouling" in root_cause
    assert confidence == "High"
    assert len(alternative_causes) >= 2
    assert len(recommended_actions) >= 2
    assert any("wash condenser coils" in r for r in recommended_actions)


def test_telemetry_endpoint_ingests_lbnl_event():
    sample_payload = {
        "event_id": "lbnl-test-001",
        "event_type": "telemetry",
        "asset_id": 7,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temperature": 16.1,
        "pressure": 31.48,
        "airflow": 97.6,
        "energy_kw": 140.58,
        "raw_data": {"condenser_temp_c": 41.28},
    }

    response = client.post("/api/v1/telemetry", json=sample_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["event_id"] == "lbnl-test-001"

    get_res = client.get("/api/v1/assets/7/telemetry?limit=5")
    assert get_res.status_code == 200
    points = get_res.json()
    assert len(points) >= 1
    latest = points[-1]
    assert "pressure" in latest
    assert "temperature" in latest
