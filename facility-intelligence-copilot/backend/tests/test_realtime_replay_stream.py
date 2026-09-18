from __future__ import annotations

import json
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.services.lbnl_adapter import LBNLAdapter
from backend.app.services.digital_twin import DigitalTwinService
from backend.app.api.v1.routes.replay import REPLAY_STATE

client = TestClient(app)


def test_get_replay_state():
    """Verifies that the replay state endpoint returns accurate position and dataset metadata."""
    response = client.get("/api/v1/replay/state")
    assert response.status_code == 200
    data = response.json()

    assert "current_row" in data
    assert "total_rows" in data
    assert "status" in data
    assert "source_time" in data
    assert "active_anomaly" in data
    assert data["total_rows"] > 0


def test_replay_control_seek_and_pause():
    """Tests seeking to an arbitrary dataset point (e.g. 25,000) and pausing."""
    # Seek
    seek_res = client.post("/api/v1/replay/control", json={"action": "seek", "target_row": 25000})
    assert seek_res.status_code == 200
    seek_data = seek_res.json()
    assert seek_data["state"]["current_row"] == 25000

    # Pause
    pause_res = client.post("/api/v1/replay/control", json={"action": "pause"})
    assert pause_res.status_code == 200
    assert pause_res.json()["state"]["status"] == "PAUSED"


def test_replay_control_forward_and_rewind():
    """Tests forward and rewind relative step adjustments."""
    # Set known start
    client.post("/api/v1/replay/control", json={"action": "seek", "target_row": 5000})
    
    # Forward 1200 steps
    fwd_res = client.post("/api/v1/replay/control", json={"action": "forward", "step_size": 1200})
    assert fwd_res.status_code == 200
    assert fwd_res.json()["state"]["current_row"] == 6200

    # Rewind 500 steps
    rew_res = client.post("/api/v1/replay/control", json={"action": "rewind", "step_size": 500})
    assert rew_res.status_code == 200
    assert rew_res.json()["state"]["current_row"] == 5700


def test_replay_control_invalid_action():
    """Verifies rejection of invalid control actions."""
    res = client.post("/api/v1/replay/control", json={"action": "teleport_quantum"})
    assert res.status_code == 400


def test_realtime_stream_event_format():
    """Tests that the realtime SSE generator yields well-formed telemetry updates with twin ML diagnostics."""
    import asyncio
    from backend.app.api.v1.routes.realtime import event_generator

    async def _get_one():
        gen = event_generator()
        try:
            return await gen.__anext__()
        finally:
            await gen.aclose()

    first_chunk = asyncio.run(_get_one())
    assert first_chunk.startswith("data: ")
    payload_str = first_chunk.replace("data: ", "", 1).strip()
    event = json.loads(payload_str)
    assert event["type"] == "TELEMETRY_UPDATE"
    assert "asset_id" in event
    assert "health_score" in event
    assert "fault_diagnosis" in event
    assert "facility_status" in event
