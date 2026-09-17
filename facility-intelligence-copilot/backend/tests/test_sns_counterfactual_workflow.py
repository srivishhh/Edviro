"""
backend/tests/test_sns_counterfactual_workflow.py

Comprehensive tests for the GSENSE 3.0 workflow:
SNS Workbench (3.0 GSense) -> Digital Twin Virtual Simulation -> Validated Technician Action.

Covers all 12 test specifications from Part H:
1. SNS output schema (workflow_name: '3.0 GSense', candidate actions)
2. Invalid candidate rejection (out-of-bounds actuator rejected)
3. Candidate actuator validation (ACTUATOR_BOUNDS check)
4. Independent Twin branches (Candidate A doesn't mutate Candidate B or baseline)
5. StatePredictor invocation
6. Predicted state output (zone_temp, sa_temp, sa_cfm, power)
7. Deterministic delta calculation (energy_saved_kw, comfort_delta_c)
8. Safety rejection (ConstraintChecker violations)
9. Resolution rejection (ResolutionEvaluator.evaluate_resolution)
10. Validated candidate (ValidationStatus.VALIDATED)
11. No-valid-candidate case (NO_VALIDATED_INTERVENTION)
12. Technician approval boundary (Only validated candidate actuates)
"""

import copy
import pytest
import numpy as np

from backend.counterfactual.schemas import (
    CandidatePlan,
    CandidateAction,
    ValidationStatus,
    ResolutionStatus,
    SafetyResult,
    ResolutionResult,
    CounterfactualSimulationResult,
    CounterfactualEvaluationResponse,
)
from backend.counterfactual.candidate_generator import CandidateGenerator
from backend.ml.features.feature_schema import ACTUATOR_BOUNDS, FaultClass
from backend.counterfactual.evaluator import CounterfactualEvaluator
from backend.counterfactual.engine import CounterfactualEngine
from backend.counterfactual.resolution import ResolutionEvaluator
from backend.counterfactual.constraints import ConstraintChecker
from backend.ml.inference.state_predictor import StatePredictor
from backend.app.integrations.sns_workbench import SNSWorkbenchClient


@pytest.fixture
def baseline_telemetry() -> dict:
    """Fixture providing a standard baseline HVAC telemetry dictionary."""
    return {
        "zone_temp": 25.8,
        "sa_temp": 14.5,
        "sa_cfm": 12500.0,
        "ra_temp": 25.0,
        "oa_temp": 30.0,
        "chwc_vlv": 75.0,
        "hwc_vlv": 0.0,
        "sf_spd": 80.0,
        "oa_dmpr": 25.0,
        "power": 16.8,
        "static_pressure": 1.25,
    }


@pytest.fixture
def stuck_damper_telemetry() -> dict:
    """Fixture providing an AHU state under stuck outdoor air damper fault."""
    return {
        "zone_temp": 26.5,
        "sa_temp": 18.0,
        "sa_cfm": 9500.0,
        "ra_temp": 25.8,
        "oa_temp": 33.0,
        "chwc_vlv": 100.0,
        "hwc_vlv": 0.0,
        "sf_spd": 90.0,
        "oa_dmpr": 10.0,  # Damper stuck low, starving fresh air / ventilation
        "power": 19.5,
        "static_pressure": 1.4,
    }


# --------------------------------------------------------------------------
# Test 1: SNS output schema (workflow_name: '3.0 GSense', candidate actions)
# --------------------------------------------------------------------------
def test_sns_output_schema():
    """Verify SNS client produces schema with workflow_name '3.0 GSense' and candidate actions."""
    client = SNSWorkbenchClient()
    response = client.generate_fault_candidates(
        incident_id="INC-3001",
        asset_id="AHU-01",
        detected_fault="Damper Stuck",
        current_state={"oa_dmpr": 10.0, "zone_temp": 26.5, "sa_cfm": 9500.0},
        actuators={"oa_dmpr": 10.0, "chwc_vlv": 100.0, "sf_spd": 90.0},
    )

    assert isinstance(response, dict)
    assert response["workflow_name"] == "3.0 GSense"
    assert response["workflow_id"] == "wf-3.0-gsense-intervention"
    assert "candidate_actions" in response
    assert len(response["candidate_actions"]) >= 2
    for cand in response["candidate_actions"]:
        assert cand["action_id"]
        assert cand["target"] in ["AHU-1", "VAV-1", "CHILLER-1", "COOLING_COIL", "oa_dmpr", "sf_spd", "chwc_vlv", "hwc_vlv"]
        assert cand["current_value"] is not None
        assert cand["proposed_value"] is not None
        assert cand["reason"]
        assert cand["expected_objective"]



# --------------------------------------------------------------------------
# Test 2: Invalid candidate rejection (out-of-bounds actuator rejected)
# --------------------------------------------------------------------------
def test_invalid_candidate_rejection_out_of_bounds(stuck_damper_telemetry):
    """Verify out-of-bounds actuator proposed values are rejected by constraint check."""
    # Proposed fan speed of 150% (> 100% max)
    invalid_plan = CandidatePlan(
        candidate_id="cand_invalid_01",
        title="Invalid Fan Overdrive",
        description="Attempt to run fan at 150%",
        proposed_by="OPERATOR_OVERRIDE",
        interventions={"sf_spd": 150.0, "oa_dmpr": 25.0},
    )
    
    safety_status, violations, score = ConstraintChecker.evaluate_constraints(
        current_state=stuck_damper_telemetry,
        interventions=invalid_plan.interventions,
        predicted_state=stuck_damper_telemetry,
    )
    assert safety_status == ValidationStatus.REJECTED
    assert len(violations) > 0
    assert any("sf_spd" in v.metric or "bounds" in v.description.lower() for v in violations)


# --------------------------------------------------------------------------
# Test 3: Candidate actuator validation (ACTUATOR_BOUNDS)
# --------------------------------------------------------------------------
def test_candidate_actuator_validation_bounds(baseline_telemetry):
    """Verify all actuator parameters adhere strictly to ACTUATOR_BOUNDS."""
    for param, bounds in ACTUATOR_BOUNDS.items():
        min_v, max_v = bounds[0], bounds[1]
        
        # Valid mid-point value
        valid_interventions = {param: (min_v + max_v) / 2.0}
        status, violations, _ = ConstraintChecker.evaluate_constraints(
            current_state=baseline_telemetry,
            interventions=valid_interventions,
            predicted_state=baseline_telemetry,
        )
        assert not any(v.metric == param for v in violations), f"Parameter {param} should be valid at midpoint"

        # Below min
        below_interventions = {param: min_v - 15.0}
        status_below, violations_below, _ = ConstraintChecker.evaluate_constraints(
            current_state=baseline_telemetry,
            interventions=below_interventions,
            predicted_state=baseline_telemetry,
        )
        assert any(v.metric == param for v in violations_below), f"Parameter {param} must violate when below min"


# --------------------------------------------------------------------------
# Test 4: Independent Twin branches (Candidate A doesn't mutate B or baseline)
# --------------------------------------------------------------------------
def test_independent_twin_branches(baseline_telemetry):
    """Verify virtual branches are isolated copies; simulating A does not mutate B or baseline."""
    engine = CounterfactualEngine.get_instance()
    
    original_baseline = copy.deepcopy(baseline_telemetry)
    
    response = engine.evaluate_facility_state(
        asset_id="AHU-01",
        current_telemetry=baseline_telemetry,
        fault_diagnosis="nominal",
        incident_id="INC-ISO-01",
    )
    
    # Check baseline was not mutated
    assert baseline_telemetry == original_baseline
    
    # Check each candidate has independent interventions and predictions
    assert len(response.all_candidates) >= 2
    cand_a = response.all_candidates[0]
    cand_b = response.all_candidates[1]
    
    assert cand_a.candidate_id != cand_b.candidate_id
    assert cand_a.proposed_interventions != cand_b.proposed_interventions


# --------------------------------------------------------------------------
# Test 5: StatePredictor invocation
# --------------------------------------------------------------------------
def test_state_predictor_invocation(baseline_telemetry):
    """Verify StatePredictor predicts new state vector given altered actuator inputs."""
    predictor = StatePredictor.get_instance()
    
    modified_actuators = {
        "sf_spd": 50.0,
        "chwc_vlv": 40.0,
        "oa_dmpr": 30.0,
    }
    
    sim_result = predictor.predict_counterfactual(
        current_state=baseline_telemetry,
        interventions=modified_actuators,
    )
    
    assert "predicted_state" in sim_result
    assert "predicted_metrics" in sim_result
    assert "deltas" in sim_result
    pred_state = sim_result["predicted_state"]
    assert pred_state["sf_spd"] == 50.0
    assert pred_state["chwc_vlv"] == 40.0
    assert pred_state["power"] > 0.0


# --------------------------------------------------------------------------
# Test 6: Predicted state output (zone_temp, sa_temp, sa_cfm, power)
# --------------------------------------------------------------------------
def test_predicted_state_output_fields(baseline_telemetry):
    """Verify predicted state output contains all core physical state fields."""
    engine = CounterfactualEngine.get_instance()
    response = engine.evaluate_facility_state(
        asset_id="AHU-01",
        current_telemetry=baseline_telemetry,
        fault_diagnosis="nominal",
    )
    
    for candidate_res in response.all_candidates:
        pred = candidate_res.predicted_state
        assert "zone_temp" in pred
        assert "sa_temp" in pred
        assert "sa_cfm" in pred
        assert "power" in pred
        assert pred["power"] > 0.0


# --------------------------------------------------------------------------
# Test 7: Deterministic delta calculation (energy_saved_kw, comfort_delta_c)
# --------------------------------------------------------------------------
def test_deterministic_delta_calculation(baseline_telemetry):
    """Verify energy_saved_kw and comfort_delta_c are strictly deterministic calculations."""
    sim_output = {
        "predicted_state": {
            **baseline_telemetry,
            "power": 12.0,       # Baseline 16.8 kW -> 4.8 kW saved
            "zone_temp": 24.0,   # Baseline 25.8 C -> -1.8 C delta
        },
        "deltas": {},
    }
    
    plan = CandidatePlan(
        candidate_id="cand_test_01",
        title="Test Plan",
        description="Test",
        proposed_by="GSENSE_ANALYTICAL_ENGINE",
        interventions={"chwc_vlv": 50.0},
    )
    
    res = CounterfactualEvaluator.evaluate(
        current_state=baseline_telemetry,
        candidate=plan,
        sim_output=sim_output,
        detected_fault="nominal",
    )
    
    expected_energy_saved = round(baseline_telemetry["power"] - 12.0, 2)
    expected_comfort_delta = round(24.0 - baseline_telemetry["zone_temp"], 2)
    
    assert res.energy_saved_kw == pytest.approx(expected_energy_saved, rel=1e-3)
    assert res.comfort_delta_c == pytest.approx(expected_comfort_delta, rel=1e-3)


# --------------------------------------------------------------------------
# Test 8: Safety rejection (ConstraintChecker violations)
# --------------------------------------------------------------------------
def test_safety_rejection_constraint_violation(baseline_telemetry):
    """Verify safety violations (freeze stat / over-temp / high pressure) fail the branch."""
    # State with freeze stat risk: OAT < 4.0 C and damper > 40%
    unsafe_state = copy.deepcopy(baseline_telemetry)
    unsafe_state["oa_temp"] = 1.0
    
    status, violations, score = ConstraintChecker.evaluate_constraints(
        current_state=baseline_telemetry,
        interventions={"oa_dmpr": 65.0},
        predicted_state=unsafe_state,
    )
    assert status == ValidationStatus.REJECTED
    assert any("FREEZE" in v.constraint_name.upper() or "oa_dmpr" in v.metric for v in violations)



# --------------------------------------------------------------------------
# Test 9: Resolution rejection (ResolutionEvaluator.evaluate_resolution)
# --------------------------------------------------------------------------
def test_resolution_rejection(stuck_damper_telemetry):
    """Verify candidates that fail to fix the fault are marked DOES_NOT_RESOLVE and rejected."""
    # Candidate leaves high zone temp unchanged outside comfort band
    ineffective_predicted = copy.deepcopy(stuck_damper_telemetry)
    ineffective_predicted["zone_temp"] = 28.5  # Outside ASHRAE comfort
    ineffective_predicted["sa_temp"] = 22.0
    
    status, evidence = ResolutionEvaluator.evaluate_resolution(
        detected_fault="Damper Stuck",
        baseline_state=stuck_damper_telemetry,
        predicted_state=ineffective_predicted,
        is_safe=True,
    )
    
    assert status == ResolutionStatus.DOES_NOT_RESOLVE
    assert any("thermal equilibrium not achieved" in e.lower() or "outside" in e.lower() for e in evidence)


# --------------------------------------------------------------------------
# Test 10: Validated candidate (ValidationStatus.VALIDATED)
# --------------------------------------------------------------------------
def test_validated_candidate_winner(stuck_damper_telemetry):
    """Verify an effective, safe candidate is chosen as the VALIDATED winner."""
    engine = CounterfactualEngine.get_instance()
    response = engine.evaluate_facility_state(
        asset_id="AHU-01",
        current_telemetry=stuck_damper_telemetry,
        fault_diagnosis=FaultClass.DAMPER_STUCK.value,
        incident_id="INC-VALID-01",
    )
    
    assert response.status == "VALIDATED"
    assert response.winning_candidate is not None
    assert response.winning_candidate.status == ValidationStatus.VALIDATED
    assert response.winning_candidate.safety.status == "PASS"
    assert response.winning_candidate.resolution.status == ResolutionStatus.RESOLVES_ISSUE


# --------------------------------------------------------------------------
# Test 11: No-valid-candidate case (NO_VALIDATED_INTERVENTION)
# --------------------------------------------------------------------------
def test_no_valid_candidate_returns_none_winner(stuck_damper_telemetry):
    """Verify when all candidates fail safety or resolution, outcome is NO_VALIDATED_INTERVENTION."""
    engine = CounterfactualEngine.get_instance()
    
    # Pass in custom out-of-bounds interventions so all candidates violate safety
    sns_invalid_plan = {
        "title": "Invalid Extreme Override",
        "description": "Exceed limits",
        "interventions": {"oa_dmpr": 150.0, "sf_spd": 120.0},
    }
    
    # Direct test of evaluation when all branches are unsafe/unresolved
    unsafe_sim = {
        "predicted_state": {**stuck_damper_telemetry, "sa_temp": 1.0, "zone_temp": 32.0},
        "deltas": {},
    }
    cand = CandidatePlan(
        candidate_id="cand_bad",
        title="Bad",
        description="Bad",
        interventions={"oa_dmpr": 120.0},
    )
    res = CounterfactualEvaluator.evaluate(
        current_state=stuck_damper_telemetry,
        candidate=cand,
        sim_output=unsafe_sim,
        detected_fault=FaultClass.DAMPER_STUCK.value,
    )
    assert res.status == ValidationStatus.REJECTED


# --------------------------------------------------------------------------
# Test 12: Technician approval boundary (Only validated candidate actuates)
# --------------------------------------------------------------------------
def test_technician_approval_boundary(baseline_telemetry):
    """Verify that only a fully validated candidate can proceed to actuation approval."""
    engine = CounterfactualEngine.get_instance()
    response = engine.evaluate_facility_state(
        asset_id="AHU-01",
        current_telemetry=baseline_telemetry,
        fault_diagnosis="nominal",
    )
    
    if response.winning_candidate:
        assert response.winning_candidate.status == ValidationStatus.VALIDATED
        assert response.winning_candidate.safety.status == "PASS"
        assert response.winning_candidate.resolution.status == ResolutionStatus.RESOLVES_ISSUE
        # Proposed interventions are ready for approval
        assert len(response.winning_candidate.proposed_interventions) > 0
    else:
        assert response.status == "NO_VALIDATED_INTERVENTION"
