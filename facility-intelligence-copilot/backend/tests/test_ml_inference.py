import pytest
from backend.ml.inference.fault_predictor import FaultPredictor
from backend.ml.inference.state_predictor import StatePredictor
from backend.ml.features.feature_schema import FaultClass


def test_fault_predictor_inference():
    predictor = FaultPredictor.get_instance()
    
    # Nominal case
    nominal_reading = {
        "oa_temp": 22.0, "ra_temp": 23.0, "ma_temp": 22.5, "sa_temp": 14.0,
        "zone_temp": 22.5, "oa_dmpr": 20.0, "chwc_vlv": 30.0, "sf_spd": 65.0,
        "sa_cfm": 2400.0, "sa_sp": 1.4, "power": 7.5
    }
    pred = predictor.predict(nominal_reading)
    assert "fault_class" in pred
    assert "fault_probability" in pred
    assert pred["fault_probability"] >= 0.0

    # Damper stuck case
    stuck_damper_reading = {
        "oa_temp": 34.0, "ra_temp": 24.0, "ma_temp": 32.5, "sa_temp": 22.0,
        "zone_temp": 26.5, "oa_dmpr": 90.0, "chwc_vlv": 100.0, "sf_spd": 85.0,
        "sa_cfm": 2500.0, "sa_sp": 1.5, "power": 14.8
    }
    pred_fault = predictor.predict(stuck_damper_reading)
    assert pred_fault["is_anomalous"] is True
    assert len(pred_fault["indicators"]) > 0


def test_state_predictor_counterfactual_deltas():
    predictor = StatePredictor.get_instance()
    
    current_state = {
        "oa_temp": 30.0, "ra_temp": 24.0, "ma_temp": 28.0, "sa_temp": 20.0,
        "zone_temp": 25.5, "oa_dmpr": 80.0, "chwc_vlv": 90.0, "sf_spd": 80.0,
        "sa_cfm": 2500.0, "sa_sp": 1.5, "power": 13.0
    }
    interventions = {"oa_dmpr": 15.0, "chwc_vlv": 45.0, "sf_spd": 70.0}

    cf_res = predictor.predict_counterfactual(current_state, interventions)
    assert "predicted_state" in cf_res
    assert "deltas" in cf_res
    assert "delta_zone_temp" in cf_res["deltas"]
    assert "delta_power_kw" in cf_res["deltas"]
    assert "energy_saved_pct" in cf_res["deltas"]
