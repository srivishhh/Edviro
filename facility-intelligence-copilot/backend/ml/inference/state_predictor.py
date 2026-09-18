from __future__ import annotations

import os
import json
import logging
from typing import Dict, Any, Optional, List
import joblib
import numpy as np

from backend.ml.features.feature_schema import (
    STATE_REGRESSOR_INPUT_FEATURES,
    STATE_REGRESSOR_TARGETS,
)
from backend.ml.features.feature_engineering import (
    validate_telemetry_dict,
    canonicalize_telemetry_dict,
    extract_features_dict,
)

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "state_regressors.joblib")
META_PATH = os.path.join(ARTIFACTS_DIR, "state_regressors_meta.json")


class StatePredictor:
    """
    Hardened ML Counterfactual State Regressor for GSENSE 3.0.
    Predicts virtual thermodynamic and energy response under simulated actuator interventions.
    """
    _instance: Optional["StatePredictor"] = None

    def __init__(self, model_path: str = MODEL_PATH, meta_path: str = META_PATH):
        self.model_path = model_path
        self.meta_path = meta_path
        self.models: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self._load_models()

    @classmethod
    def get_instance(cls) -> "StatePredictor":
        if cls._instance is None:
            cls._instance = StatePredictor()
        return cls._instance

    def _load_models(self) -> None:
        if os.path.exists(self.model_path):
            try:
                self.models = joblib.load(self.model_path)
                if os.path.exists(self.meta_path):
                    with open(self.meta_path, "r", encoding="utf-8") as f:
                        self.metadata = json.load(f)
                logger.info(f"Loaded Counterfactual State Regressors from {self.model_path}")
                return
            except Exception as e:
                logger.error(f"Error loading state regressors: {e}")
                self.models = {}
        else:
            logger.warning(f"State regressors artifact not found at {self.model_path}")
            self.models = {}

    def predict_counterfactual(
        self,
        current_state: Dict[str, Any],
        interventions: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Predicts next state and deltas given current telemetry and candidate actuator changes.
        """
        validate_telemetry_dict(current_state)
        canonical = canonicalize_telemetry_dict(current_state)

        # Apply intervention onto candidate actuator state
        simulated_state = dict(canonical)
        for act, val in interventions.items():
            act_clean = act.strip().lower()
            if act_clean in simulated_state:
                simulated_state[act_clean] = float(val)

        # Check if incoming telemetry temperatures are in Celsius (infer strictly from indoor zone/return/supply channels)
        is_celsius = False
        for t_key in ["zone_temp", "ra_temp", "sa_temp"]:
            if t_key in canonical:
                try:
                    if float(canonical[t_key]) <= 45.0:
                        is_celsius = True
                        break
                except (ValueError, TypeError):
                    pass

        working_state = dict(simulated_state)
        temp_keys = ["oa_temp", "ra_temp", "ma_temp", "sa_temp", "zone_temp"]
        if is_celsius:
            for tk in temp_keys:
                if tk in working_state:
                    working_state[tk] = working_state[tk] * 9.0 / 5.0 + 32.0

        # Build strictly ordered input vector (in Fahrenheit domain matching LBNL weights)
        vec = [working_state.get(feat, 0.0) for feat in STATE_REGRESSOR_INPUT_FEATURES]
        x_in = np.array([vec], dtype=np.float32)

        predicted_targets: Dict[str, float] = {}

        if self.models and all(t in self.models for t in STATE_REGRESSOR_TARGETS):
            for target_name, model in self.models.items():
                try:
                    val = float(model.predict(x_in)[0])
                    # If input was Celsius and target is a temperature channel, convert back to Celsius
                    if is_celsius and target_name in ["zone_temp", "sa_temp"]:
                        val = (val - 32.0) * 5.0 / 9.0
                    predicted_targets[target_name] = round(val, 2)
                except Exception as e:
                    logger.error(f"Error predicting target {target_name}: {e}")
                    predicted_targets[target_name] = self._physics_approx(canonical, simulated_state, target_name, is_celsius)
        else:
            for target_name in STATE_REGRESSOR_TARGETS:
                predicted_targets[target_name] = self._physics_approx(canonical, simulated_state, target_name, is_celsius)

        # Calculate differential impacts
        cur_temp = canonical.get("zone_temp", 22.0 if is_celsius else 72.0)
        pred_temp = predicted_targets.get("zone_temp", cur_temp)
        delta_temp = round(pred_temp - cur_temp, 2)

        cur_power = canonical.get("power", 8.5)
        pred_power = predicted_targets.get("power", cur_power)
        delta_power = round(pred_power - cur_power, 2)
        power_saved_pct = round(-100.0 * delta_power / max(cur_power, 0.1), 1)

        cur_cfm = canonical.get("sa_cfm", 2500.0)
        pred_cfm = predicted_targets.get("sa_cfm", cur_cfm)
        delta_cfm = round(pred_cfm - cur_cfm, 1)

        return {
            "predicted_state": {
                **simulated_state,
                **predicted_targets,
            },
            "predicted_metrics": predicted_targets,
            "deltas": {
                "delta_zone_temp": delta_temp,
                "delta_power_kw": delta_power,
                "energy_saved_pct": power_saved_pct,
                "delta_sa_cfm": delta_cfm,
            },
            "applied_interventions": interventions,
        }

    def _physics_approx(self, orig: Dict[str, float], sim: Dict[str, float], target: str, is_celsius: bool = False) -> float:
        oa = sim.get("oa_temp", 20.0 if is_celsius else 65.0)
        ra = sim.get("ra_temp", 22.0 if is_celsius else 72.0)
        oad = sim.get("oa_dmpr", 20.0)
        chwc = sim.get("chwc_vlv", 35.0)
        spd = sim.get("sf_spd", 70.0)
        cool_drop = 8.3 if is_celsius else 15.0
        target_ref = 22.0 if is_celsius else 72.0

        if target == "sa_temp":
            mat = (oad / 100.0) * oa + ((100.0 - oad) / 100.0) * ra
            return round(mat - (chwc / 100.0) * cool_drop, 2)
        elif target == "sa_cfm":
            return round(spd * 35.0, 1)
        elif target == "power":
            return round(0.8 + (spd / 100.0) ** 2.8 * 6.5 + (chwc / 100.0) * 5.0, 2)
        elif target == "zone_temp":
            mat = (oad / 100.0) * oa + ((100.0 - oad) / 100.0) * ra
            sat = mat - (chwc / 100.0) * cool_drop
            return round(ra + 0.3 * (oa - target_ref) / 10.0 - (spd / 100.0) * (target_ref - sat) * 0.1, 2)
        return 0.0
