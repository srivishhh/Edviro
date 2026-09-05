from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.schemas.incident_graph import NodeType
from app.services.incident_graph_service import IncidentGraphService
from main import app

client = TestClient(app)


def test_1_list_incident_relationships():
    """Test 1: GET /api/v1/incidents/relationships returns list of incident summaries."""
    resp = client.get("/api/v1/incidents/relationships")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    # Verify summary fields
    first = data[0]
    assert "incident_id" in first
    assert "incident_name" in first
    assert "severity" in first
    assert "confidence" in first
    assert "affected_components_count" in first
    assert "possible_causes_count" in first
    assert "energy_impact" in first


def test_2_get_incident_relationship_graph_airflow_restriction():
    """Test 2: GET /api/v1/incidents/101/relationships returns rich causal DAG."""
    resp = client.get("/api/v1/incidents/101/relationships")
    assert resp.status_code == 200
    data = resp.json()

    assert "summary" in data
    assert "nodes" in data
    assert "edges" in data
    assert "historical_matches" in data

    nodes = data["nodes"]
    edges = data["edges"]
    node_types = {n["type"] for n in nodes}

    # Verify all core required node types are present
    assert NodeType.ASSET.value in node_types
    assert NodeType.SENSOR.value in node_types
    assert NodeType.ANOMALY.value in node_types
    assert NodeType.COMPONENT.value in node_types
    assert NodeType.ROOT_CAUSE.value in node_types
    assert NodeType.IMPACT.value in node_types
    assert NodeType.ACTION.value in node_types

    # Check that components include Filter, Damper, Fan, Cooling Coil
    labels = [n["label"] for n in nodes]
    assert any("Filter" in l for l in labels)
    assert any("Damper" in l for l in labels)
    assert any("Cooling Coil" in l for l in labels)
    assert any("Fan" in l for l in labels)

    # Check relationships
    edge_rels = {e["relationship"] for e in edges}
    assert "reports_anomaly" in edge_rels
    assert "associated_with" in edge_rels
    assert "depends_on" in edge_rels
    assert "caused_by" in edge_rels
    assert "produces" in edge_rels
    assert "requires" in edge_rels

    # Check telemetry attached to sensors
    sensors = [n for n in nodes if n["type"] == NodeType.SENSOR.value]
    assert len(sensors) >= 3
    for s in sensors:
        assert s["telemetry"] is not None
        assert "current_value" in s["telemetry"]
        assert "expected_range" in s["telemetry"]


def test_3_get_incident_relationship_graph_condenser_fouling():
    """Test 3: GET /api/v1/incidents/104/relationships returns condenser fouling DAG."""
    resp = client.get("/api/v1/incidents/104/relationships")
    assert resp.status_code == 200
    data = resp.json()

    assert data["summary"]["alert_type"] == "CONDENSER_FOULING"
    assert data["summary"]["severity"] == "CRITICAL"

    nodes = data["nodes"]
    labels = [n["label"] for n in nodes]
    assert any("Condenser" in l for l in labels)

    # Check head pressure sensor
    press_sensor = next((n for n in nodes if n["id"] == "sensor_pressure"), None)
    assert press_sensor is not None
    assert "31.5" in str(press_sensor["telemetry"]["current_value"])


def test_4_facility_memory_matches():
    """Test 4: Verifies similar historical incidents match Facility Memory (#104, #089, #074)."""
    resp = client.get("/api/v1/incidents/101/relationships")
    assert resp.status_code == 200
    data = resp.json()

    matches = data["historical_matches"]
    assert len(matches) >= 3
    memory_ids = {m["memory_id"] for m in matches}
    assert "MEM-2026-104" in memory_ids
    assert "MEM-2026-089" in memory_ids
    assert "MEM-2026-074" in memory_ids

    # Similarity percentages
    similarities = [m["similarity_pct"] for m in matches]
    assert any(s >= 90 for s in similarities)


def test_5_alias_route_and_string_fallback():
    """Test 5: Checks alias /api/incidents/{id}/relationships and fallback on string ID."""
    resp1 = client.get("/api/incidents/101/relationships")
    assert resp1.status_code == 200

    resp2 = client.get("/api/v1/incidents/invalid-str-id/relationships")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert "summary" in data2
    assert len(data2["nodes"]) > 0


def test_6_zero_side_effects_read_only():
    """Test 6: Guarantees that generating relationship graphs causes zero mutations."""
    from app.api.v1.routes.telemetry import TWIN_LIBRARY

    twin_before = dict(TWIN_LIBRARY[7]["current_state"])

    service = IncidentGraphService()
    for inc_id in [101, 102, 103, 104, 105]:
        graph = service.get_incident_relationship_graph(inc_id)
        assert graph.summary is not None
        assert len(graph.nodes) > 0

    twin_after = dict(TWIN_LIBRARY[7]["current_state"])
    assert twin_before == twin_after, "Digital Twin state must remain untouched (READ-ONLY)!"
