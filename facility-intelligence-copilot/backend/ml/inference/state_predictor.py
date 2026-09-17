from __future__ import annotations

import os
import json
import logging
from typing import Dict, Any, Optional, List
import joblib
import numpy as np

from backend.ml.features.feature_engineering import canonicalize_telemetry_dict, extract_features_dict
from backend.ml.training.train_state_model import STATE_CF_INPUT_FEATURES, STATE_CF_TARGET_CHANNELS

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "state_regressors.joblib")
META_PATH = os.path.join(ARTIFACTS_DIR, "state_regressors_meta.json")


class StatePredictor:
    """
    ML-driven Counterfactual State Regressor for GSENSE 3.0.
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
        if os.path.exists(self.model_path) and os.path.exists(self.meta_path):
            try:
                self.models = joblib.load(self.model_path)
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded Counterfactual State Regressors from {self.model_path}")
                return
            except Exception as e:
                logger.error(f"Error loading state regressors: {e}. Attempting on-demand training.")

        try:
            from backend.ml.training.train_state_model import train_counterfactual_state_models
            logger.info("State model artifacts not found. Training on LBNL dataset...")
            self.models, self.metadata = train_counterfactual_state_models(artifacts_dir=ARTIFACTS_DIR)
        except Exception as e:
            logger.error(f"Failed to train state regressors on demand: {e}")
            self.models = {}

    def predict_counterfactual(
        self,
        current_state: Dict[str, Any],
        interventions: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Predicts next state and deltas given current telemetry and candidate actuator changes.
        """
        canonical = canonicalize_telemetry_dict(current_state)
        
        # Apply intervention onto candidate actuator state
        simulated_state = dict(canonical)
        for act, val in interventions.items():
            act_clean = act.strip().lower()
            if act_clean in simulated_state:
                simulated_state[act_clean] = float(val)

        # Build feature vector
        vec = [simulated_state.get(feat, 0.0) for feat in STATE_CF_INPUT_FEATURES]
        x_in = np.array([vec], dtype=np.float32)

        predicted_targets: Dict[str, float] = {}

        if self.models and all(t in self.models for t in STATE_CF_TARGET_CHANNELS):
            for target_name, model in self.models.items():
                try:
                    val = float(model.predict(x_in)[0])
                    predicted_targets[target_name] = round(val, 2)
                except Exception as e:
                    logger.error(f"Error predicting target {target_name}: {e}")
                    predicted_targets[target_name] = self._physics_approx(canonical, simulated_state, target_name)
        else:
            # First-principles thermodynamic fallback
            for target_name in STATE_CF_TARGET_CHANNELS:
                predicted_targets[target_name] = self._physics_approx(canonical, simulated_state, target_name)

        # Calculate differential impacts
        cur_temp = canonical.get("zone_temp", 22.8)
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

    def _physics_approx(self, orig: Dict[str, float], sim: Dict[str, float], target: str) -> float:
        """Physical first-principles approximation if regressor weights are offline."""
        oa = sim.get("oa_temp", 24.0)
        ra = sim.get("ra_temp", 23.0)
        oad = sim.get("oa_dmpr", 25.0)
        chwc = sim.get("chwc_vlv", 35.0)
        spd = sim.get("sf_spd", 70.0)

        if target == "sa_temp":
            mat = (oad / 100.0) * oa + ((100.0 - oad) / 100.0) * ra
            return round(mat - (chwc / 100.0) * 11.5, 2)
        elif target == "sa_cfm":
            return round(spd * 35.0, 1)
        elif target == "power":
            return round(0.8 + (spd / 100.0) ** 2.8 * 6.5 + (chwc / 100.0) * 5.0, 2)
        elif target == "zone_temp":
            mat = (oad / 100.0) * oa + ((100.0 - oad) / 100.0) * ra
            sat = mat - (chwc / 100.0) * 11.5
            return round(ra + 0.3 * (oa - 22.0) / 10.0 - (spd / 100.0) * (23.0 - sat) * 0.1, 2)
        return 0.0
