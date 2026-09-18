from __future__ import annotations

import os
import json
import pytest
import numpy as np

from backend.ml.features.feature_schema import (
    FaultClass,
    FAULT_INT_TO_LABEL,
    FAULT_LABEL_TO_INT,
    ALL_FAULT_FEATURES,
    STATE_REGRESSOR_INPUT_FEATURES,
    STATE_REGRESSOR_TARGETS,
)
from backend.ml.features.feature_engineering import (
    validate_telemetry_dict,
    canonicalize_telemetry_dict,
    compute_derived_features,
    extract_features_dict,
    extract_feature_vector,
)
from backend.ml.inference.fault_predictor import FaultPredictor
from backend.ml.inference.state_predictor import StatePredictor


# ---------------------------------------------------------------------------
# 1. Feature Generation & Validation Tests
# ---------------------------------------------------------------------------

def test_feature_generation_deterministic_order():
    raw_sample = {
        "OA_TEMP": 75.2,
        "RA_TEMP": 72.0,
        "MA_TEMP": 73.1,
        "SA_TEMP": 56.4,
        "ZONE_TEMP_1": 71.8,
        "ZONE_TEMP_2": 72.2,
        "ZONE_TEMP_3": 72.0,
        "ZONE_TEMP_4": 71.9,
        "ZONE_TEMP_5": 72.1,
        "OA_DMPR": 0.25,
        "RA_DMPR": 0.75,
        "CHWC_VLV": 0.40,
        "SF_SPD": 0.85,
        "SF_WAT": 650.0,
        "RF_WAT": 250.0,
        "SA_CFM": 2800.0,
        "SA_SP": 1.65,
    }

    fdict = extract_features_dict(raw_sample)
    assert "delta_t_coil" in fdict
    assert "delta_t_mixed" in fdict
    assert "mixed_air_ratio" in fdict
    assert "thermal_load_proxy" in fdict
    assert "airflow_per_speed" in fdict
    assert "sp_per_speed" in fdict
    assert "power_per_airflow" in fdict
    assert "damper_cooling_fight" in fdict

    # Zone average was computed correctly
    assert abs(fdict["zone_temp"] - 72.0) < 0.1
    # Fan power was converted to kW
    assert abs(fdict["power"] - 0.90) < 0.01

    vec1 = extract_feature_vector(raw_sample, ALL_FAULT_FEATURES)
    vec2 = extract_feature_vector(raw_sample, ALL_FAULT_FEATURES)
    assert len(vec1) == len(ALL_FAULT_FEATURES)
    np.testing.assert_array_equal(vec1, vec2)


def test_validation_rejects_corrupted_telemetry():
    # Empty dict
    with pytest.raises(ValueError, match="empty"):
        validate_telemetry_dict({})

    # NaN detection
    with pytest.raises(ValueError, match="NaN"):
        validate_telemetry_dict({"oa_temp": float("nan"), "sa_temp": 55.0})

    # Inf detection
    with pytest.raises(ValueError, match="Inf"):
        validate_telemetry_dict({"oa_temp": float("inf"), "sa_temp": 55.0})


# ---------------------------------------------------------------------------
# 2. Model Loading & Metadata Integrity Tests
# ---------------------------------------------------------------------------

def test_model_artifacts_and_metadata_exist():
    artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml", "artifacts")
    meta_path = os.path.join(artifacts_dir, "model_metadata.json")

    assert os.path.exists(meta_path), f"Metadata missing at {meta_path}"
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert "training_timestamp" in meta
    assert "dataset_files" in meta
    assert "split_strategy" in meta
    assert "row_counts" in meta
    assert meta["row_counts"]["train_rows"] > 0
    assert meta["row_counts"]["test_rows"] > 0
    assert "models" in meta
    assert "fault_classifier" in meta["models"]
    assert "state_regressors" in meta["models"]


def test_fault_predictor_inference_contract():
    predictor = FaultPredictor.get_instance()

    nominal_input = {
        "oa_temp": 65.0, "ra_temp": 72.0, "ma_temp": 68.0, "sa_temp": 55.0,
        "zone_temp": 72.0, "oa_dmpr": 20.0, "chwc_vlv": 35.0, "sf_spd": 70.0,
        "sa_cfm": 2500.0, "sa_sp": 1.5, "power": 8.5
    }

    res = predictor.predict(nominal_input)
    assert "fault_class" in res
    assert "fault_probability" in res
    assert "all_probabilities" in res
    assert "confidence" in res
    assert "indicators" in res
    assert isinstance(res["fault_probability"], float)
    assert 0.0 <= res["fault_probability"] <= 1.0


def test_state_predictor_inference_contract():
    predictor = StatePredictor.get_instance()

    current_state = {
        "oa_temp": 85.0, "ra_temp": 74.0, "ma_temp": 80.0, "sa_temp": 65.0,
        "zone_temp": 75.0, "oa_dmpr": 80.0, "chwc_vlv": 90.0, "sf_spd": 80.0,
        "sa_cfm": 2500.0, "sa_sp": 1.5, "power": 12.5
    }
    interventions = {"oa_dmpr": 15.0, "chwc_vlv": 45.0, "sf_spd": 70.0}

    res = predictor.predict_counterfactual(current_state, interventions)
    assert "predicted_state" in res
    assert "predicted_metrics" in res
    assert "deltas" in res
    for tgt in STATE_REGRESSOR_TARGETS:
        assert tgt in res["predicted_metrics"]
    assert "delta_zone_temp" in res["deltas"]
    assert "delta_power_kw" in res["deltas"]
    assert "energy_saved_pct" in res["deltas"]


def test_deterministic_predictions_invariance():
    fp = FaultPredictor.get_instance()
    sp = StatePredictor.get_instance()

    state = {
        "oa_temp": 68.0, "ra_temp": 72.0, "ma_temp": 70.0, "sa_temp": 56.0,
        "zone_temp": 72.0, "oa_dmpr": 25.0, "chwc_vlv": 40.0, "sf_spd": 75.0,
        "sa_cfm": 2600.0, "sa_sp": 1.5, "power": 7.8
    }

    res1_fp = fp.predict(state)
    res2_fp = fp.predict(state)
    assert res1_fp["fault_class"] == res2_fp["fault_class"]
    assert res1_fp["fault_probability"] == res2_fp["fault_probability"]

    res1_sp = sp.predict_counterfactual(state, {"chwc_vlv": 50.0})
    res2_sp = sp.predict_counterfactual(state, {"chwc_vlv": 50.0})
    assert res1_sp["predicted_metrics"] == res2_sp["predicted_metrics"]
