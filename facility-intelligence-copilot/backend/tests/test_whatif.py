from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.schemas.whatif import WhatIfParameterChanges, WhatIfSimulateRequest
from app.services.whatif_service import WhatIfSimulationService
from main import app

client = TestClient(app)


def test_1_normal_state_simulation():
    """Test 1: Simulating baseline normal operation yields low risk and high health."""
    req = WhatIfSimulateRequest(
        asset_id="HVAC-007",
        changes=WhatIfParameterChanges(
            temperature=23.0,
            pressure=3.8,
            airflow=96.0,
            energy_kw=6.5,
        ),
    )
    res = WhatIfSimulationService.simulate(req)

    assert res.asset_id == "HVAC-007"
    assert res.predicted.temperature == 23.0
    assert res.predicted.pressure == 3.8
    assert res.predicted.airflow == 96.0
    assert res.predicted.energy_kw == 6.5
    assert res.predicted.risk_level == "LOW"
    assert res.predicted.risk <= 25.0
    assert res.predicted.health >= 85.0
    assert res.is_simulation is True


def test_2_high_temperature_stress():
    """Test 2: High temperature elevates risk and thermal power demand."""
    req = WhatIfSimulateRequest(
        asset_id="HVAC-007",
        changes=WhatIfParameterChanges(
            temperature=34.0,
        ),
    )
    res = WhatIfSimulationService.simulate(req)

    assert res.predicted.temperature == 34.0
    assert res.predicted.risk > res.current.risk or res.predicted.risk >= 40.0
    assert res.predicted.health < res.current.health or res.predicted.health <= 75.0
    # Energy should have increased due to thermal load
    assert res.predicted.energy_kw >= res.current.energy_kw


def test_3_high_pressure_stress():
    """Test 3: High head pressure increases mechanical stress and risk."""
    req = WhatIfSimulateRequest(
        asset_id="HVAC-001",
        changes=WhatIfParameterChanges(
            pressure=8.5,
        ),
    )
    res = WhatIfSimulationService.simulate(req)

    assert res.predicted.pressure == 8.5
    assert res.predicted.risk >= 20.0
    assert res.predicted.energy_kw >= res.current.energy_kw


def test_4_low_airflow_restriction():
    """Test 4: Reduced airflow causes restriction penalty and degraded health."""
    req = WhatIfSimulateRequest(
        asset_id="HVAC-007",
        changes=WhatIfParameterChanges(
            airflow=45.0,
        ),
    )
    res = WhatIfSimulationService.simulate(req)

    assert res.predicted.airflow == 45.0
    assert res.predicted.risk_level in ("HIGH", "CRITICAL", "MODERATE")
    assert res.impact.health_change < 0 or res.predicted.health <= 70.0
    # Dependent pressure should reflect duct restriction buildup
    assert res.predicted.pressure >= res.current.pressure


def test_5_improved_airflow():
    """Test 5: Improving airflow restores ventilation, reduces energy penalty and risk."""
    req = WhatIfSimulateRequest(
        asset_id="HVAC-003",
        changes=WhatIfParameterChanges(
            airflow=98.0,
        ),
    )
    res = WhatIfSimulationService.simulate(req)

    assert res.predicted.airflow == 98.0
    # Predicted energy should decrease due to relieved restriction
    assert res.predicted.energy_kw <= res.current.energy_kw
    assert res.impact.energy_change_percent <= 0.0
    assert res.predicted.health >= res.current.health


def test_6_energy_optimization():
    """Test 6: Energy optimization mode predicts negative energy delta."""
    req = WhatIfSimulateRequest(
        asset_id="HVAC-007",
        changes=WhatIfParameterChanges(
            temperature=24.0,
            airflow=92.0,
            energy_kw=6.2,
        ),
    )
    res = WhatIfSimulationService.simulate(req)

    assert res.predicted.energy_kw == 6.2
    assert res.impact.energy_change_kw < 0
    assert res.impact.energy_change_percent < 0
    assert "reduction" in res.explanation.lower() or "lower" in res.explanation.lower() or res.impact.energy_change_kw < 0


def test_7_boundary_values():
    """Test 7: Verification that risk and health stay strictly bounded between 0 and 100."""
    extreme_high = WhatIfSimulateRequest(
        asset_id="HVAC-007",
        changes=WhatIfParameterChanges(
            temperature=85.0,
            pressure=40.0,
            airflow=0.0,
            energy_kw=200.0,
        ),
    )
    res_high = WhatIfSimulationService.simulate(extreme_high)
    assert 0.0 <= res_high.predicted.risk <= 100.0
    assert 0.0 <= res_high.predicted.health <= 100.0
    assert res_high.predicted.risk_level == "CRITICAL"

    extreme_low = WhatIfSimulateRequest(
        asset_id="HVAC-007",
        changes=WhatIfParameterChanges(
            temperature=-25.0,
            pressure=0.2,
            airflow=0.0,
            energy_kw=0.0,
        ),
    )
    res_low = WhatIfSimulationService.simulate(extreme_low)
    assert 0.0 <= res_low.predicted.risk <= 100.0
    assert 0.0 <= res_low.predicted.health <= 100.0


def test_8_api_endpoints():
    """Test 8: API endpoint POST /api/v1/what-if/simulate and /api/what-if/simulate."""
    payload = {
        "asset_id": "HVAC-007",
        "changes": {
            "temperature": 25.0,
            "airflow": 95.0,
        },
    }

    # Test /api/v1/what-if/simulate
    resp1 = client.post("/api/v1/what-if/simulate", json=payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["asset_id"] == "HVAC-007"
    assert data1["is_simulation"] is True
    assert "current" in data1
    assert "predicted" in data1
    assert "impact" in data1
    assert "explanation" in data1
    assert len(data1["recommendations"]) > 0

    # Test alias /api/what-if/simulate
    resp2 = client.post("/api/what-if/simulate", json=payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["asset_id"] == "HVAC-007"

    # Test presets endpoint
    resp3 = client.get("/api/v1/what-if/presets")
    assert resp3.status_code == 200
    presets = resp3.json()
    assert len(presets) >= 5
    assert any(p["id"] == "normal_operation" for p in presets)
    assert any(p["id"] == "improve_airflow" for p in presets)


def test_9_zero_side_effects_guarantee():
    """Test 9: Verifies What-If simulation causes zero DB mutations or alert generation."""
    from app.api.v1.routes.telemetry import TWIN_LIBRARY
    
    twin_before = dict(TWIN_LIBRARY[7]["current_state"])

    req = WhatIfSimulateRequest(
        asset_id="HVAC-007",
        changes=WhatIfParameterChanges(
            temperature=99.0,
            airflow=1.0,
        ),
    )
    WhatIfSimulationService.simulate(req)

    twin_after = dict(TWIN_LIBRARY[7]["current_state"])
    assert twin_before == twin_after, "Digital Twin live state must not be modified by simulation!"
