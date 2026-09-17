from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.services.digital_twin import DigitalTwinService
from backend.counterfactual.schemas import ValidationStatus, ProvenanceType
from backend.counterfactual.engine import CounterfactualEngine
from backend.ml.features.feature_schema import FaultClass

client = TestClient(app)


def test_get_active_incident_endpoint():
    """Verifies that the /incidents/active endpoint diagnoses state and attaches counterfactual plans."""
    response = client.get("/api/v1/incidents/active")
    assert response.status_code == 200
    data = response.json()

    assert "asset_id" in data
    assert "health_score" in data
    assert "fault_diagnosis" in data
    assert "current_telemetry" in data
    assert "counterfactual_solution" in data
    assert "has_active_incident" in data

    cf = data["counterfactual_solution"]
    assert cf["candidates_evaluated"] > 0
    assert cf["winning_candidate"] is not None
    assert "deltas" in cf["winning_candidate"]


def test_evaluate_counterfactual_endpoint_with_custom_telemetry():
    """Verifies direct counterfactual evaluation endpoint with explicitly supplied telemetry."""
    payload = {
        "asset_id": "AHU-007",
        "current_telemetry": {
            "oa_temp": 32.0,
            "ra_temp": 24.5,
            "ma_temp": 30.0,
            "sa_temp": 21.5,
            "zone_temp": 25.5,
            "oa_dmpr": 85.0,
            "chwc_vlv": 95.0,
            "sf_spd": 80.0,
            "sa_cfm": 2400.0,
            "sa_sp": 1.6,
            "power": 14.5,
        }
    }
    response = client.post("/api/v1/counterfactual/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["asset_id"] == "AHU-007"
    assert data["candidates_evaluated"] >= 2
    assert data["winning_candidate"] is not None
    assert data["winning_candidate"]["status"] in ["VALIDATED", "NEEDS_REVIEW"]
    assert "delta_power_kw" in data["winning_candidate"]["deltas"]


def test_actuation_lifecycle_and_history():
    """Verifies technician actuation approval, twin state mutation, and audit trail generation."""
    # Step 1: Initial active incident
    init_res = client.get("/api/v1/incidents/active")
    assert init_res.status_code == 200
    init_data = init_res.json()
    winning = init_data["counterfactual_solution"]["winning_candidate"]

    # Step 2: Approve & Actuate winning plan
    actuate_payload = {
        "asset_id": "AHU-007",
        "candidate_id": winning["candidate_id"],
        "interventions": winning["proposed_interventions"],
        "notes": "Approved by Facility Chief Engineer in automated Stage 2 test run",
    }
    act_res = client.post("/api/v1/incidents/actuate", json=actuate_payload)
    assert act_res.status_code == 200
    act_data = act_res.json()

    assert act_data["success"] is True
    assert "actuation_record" in act_data
    assert act_data["actuation_record"]["candidate_id"] == winning["candidate_id"]

    # Step 3: Check actuation history endpoint
    hist_res = client.get("/api/v1/incidents/actuation/history")
    assert hist_res.status_code == 200
    hist_list = hist_res.json()
    assert len(hist_list) > 0
    assert any(rec["candidate_id"] == winning["candidate_id"] for rec in hist_list)


def test_actuation_empty_interventions_rejection():
    """Ensures that empty or missing actuation payloads are cleanly rejected with HTTP 400."""
    response = client.post("/api/v1/incidents/actuate", json={"asset_id": "AHU-007", "interventions": {}})
    assert response.status_code == 400


def test_lbnl_scenario_pipeline_coi_stuck():
    """Tests full pipeline flow for a cooling coil stuck scenario."""
    twin = DigitalTwinService.get_instance()
    
    stuck_frame = {
        "oa_temp": 30.0,
        "ra_temp": 24.0,
        "ma_temp": 28.5,
        "sa_temp": 26.0,
        "zone_temp": 26.5,
        "oa_dmpr": 20.0,
        "chwc_vlv": 100.0,
        "sf_spd": 85.0,
        "sa_cfm": 2800.0,
        "sa_sp": 1.7,
        "power": 12.0,
    }
    state = twin.process_telemetry_frame("AHU-007", stuck_frame)
    assert state.asset_id == "AHU-007"

    cf_res = twin.evaluate_counterfactual("AHU-007", incident_id="INC-3002")
    assert cf_res.candidates_evaluated > 0
    assert cf_res.winning_candidate is not None
    assert cf_res.winning_candidate.audit_provenance["telemetry_source"] == ProvenanceType.SOURCE_FACT
