import pytest
from backend.counterfactual.engine import CounterfactualEngine
from backend.counterfactual.schemas import ValidationStatus, ProvenanceType
from backend.counterfactual.constraints import ConstraintChecker
from backend.ml.features.feature_schema import FaultClass


def test_constraint_checker_actuator_limits():
    current_state = {"oa_dmpr": 25.0, "zone_temp": 22.8, "sa_sp": 1.5, "power": 8.5}
    invalid_intervention = {"oa_dmpr": 125.0}  # Over 100%
    predicted_state = {"oa_dmpr": 125.0, "zone_temp": 23.0, "sa_sp": 1.5, "power": 8.5}

    status, violations, score = ConstraintChecker.evaluate_constraints(
        current_state=current_state,
        interventions=invalid_intervention,
        predicted_state=predicted_state,
    )
    assert status == ValidationStatus.REJECTED
    assert any(v.constraint_name == "PHYSICAL_ACTUATOR_LIMIT" for v in violations)


def test_constraint_checker_comfort_limits():
    current_state = {"oa_dmpr": 25.0, "zone_temp": 25.0, "sa_sp": 1.5, "power": 8.5}
    intervention = {"oa_dmpr": 20.0}
    hot_predicted_state = {"oa_dmpr": 20.0, "zone_temp": 28.5, "sa_sp": 1.5, "power": 8.5}

    status, violations, score = ConstraintChecker.evaluate_constraints(
        current_state=current_state,
        interventions=intervention,
        predicted_state=hot_predicted_state,
    )
    assert status == ValidationStatus.REJECTED
    assert any(v.constraint_name == "ASHRAE_THERMAL_COMFORT_CEILING" for v in violations)


def test_counterfactual_engine_evaluation_flow():
    engine = CounterfactualEngine.get_instance()
    telemetry = {
        "oa_temp": 32.0,
        "ra_temp": 24.5,
        "ma_temp": 30.0,
        "sa_temp": 21.5,
        "zone_temp": 26.2,
        "oa_dmpr": 85.0,
        "chwc_vlv": 95.0,
        "sf_spd": 80.0,
        "sa_cfm": 2400.0,
        "sa_sp": 1.6,
        "power": 14.5,
    }

    res = engine.evaluate_facility_state(
        asset_id="AHU-007",
        current_telemetry=telemetry,
        fault_diagnosis=FaultClass.DAMPER_STUCK.value,
        incident_id="INC-3001",
    )

    assert res.asset_id == "AHU-007"
    assert res.candidates_evaluated > 0
    assert res.winning_candidate is not None
    assert res.winning_candidate.status == ValidationStatus.VALIDATED
    assert "delta_zone_temp" in res.winning_candidate.deltas
    assert res.winning_candidate.audit_provenance["telemetry_source"] == ProvenanceType.SOURCE_FACT
