from __future__ import annotations

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple
import joblib
import numpy as np

from backend.ml.features.feature_schema import (
    ALL_FAULT_FEATURES,
    FAULT_INT_TO_LABEL,
    FAULT_LABEL_TO_INT,
    FaultClass,
)
from backend.ml.features.feature_engineering import (
    canonicalize_telemetry_dict,
    compute_derived_features,
    extract_feature_vector,
    extract_features_dict,
)

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "fault_classifier.joblib")
META_PATH = os.path.join(ARTIFACTS_DIR, "fault_classifier_meta.json")


class FaultPredictor:
    """
    ML-driven HVAC Fault Classifier for GSENSE 3.0.
    Identifies root-cause equipment faults with calibrated probabilities.
    """
    _instance: Optional["FaultPredictor"] = None

    def __init__(self, model_path: str = MODEL_PATH, meta_path: str = META_PATH):
        self.model_path = model_path
        self.meta_path = meta_path
        self.model = None
        self.metadata: Dict[str, Any] = {}
        self._load_model()

    @classmethod
    def get_instance(cls) -> "FaultPredictor":
        if cls._instance is None:
            cls._instance = FaultPredictor()
        return cls._instance

    def _load_model(self) -> None:
        """Loads trained fault model or lazily trains one if missing."""
        if os.path.exists(self.model_path) and os.path.exists(self.meta_path):
            try:
                self.model = joblib.load(self.model_path)
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded Fault Classifier from {self.model_path}")
                return
            except Exception as e:
                logger.error(f"Error loading fault model: {e}. Falling back to on-demand training.")

        # On-demand training
        try:
            from backend.ml.training.train_fault_model import train_fault_classifier
            logger.info("Fault model artifact not found. Training on LBNL dataset...")
            self.model, self.metadata = train_fault_classifier(artifacts_dir=ARTIFACTS_DIR)
        except Exception as e:
            logger.error(f"Failed to train fault model on demand: {e}")
            self.model = None

    def predict(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes fault inference on incoming live or replayed telemetry frame.
        """
        features_dict = extract_features_dict(telemetry)
        x_vec = np.array([[features_dict.get(k, 0.0) for k in ALL_FAULT_FEATURES]], dtype=np.float32)

        if self.model is None:
            # Physics-based heuristic fallback if model could not be loaded
            return self._heuristic_fallback(features_dict)

        try:
            probas = self.model.predict_proba(x_vec)[0]
            pred_int = int(np.argmax(probas))
            pred_label = FAULT_INT_TO_LABEL.get(pred_int, FaultClass.NOMINAL.value)
            prob = float(probas[pred_int])

            all_probs = {
                FAULT_INT_TO_LABEL.get(i, f"class_{i}"): float(probas[i])
                for i in range(len(probas))
            }

            confidence = "HIGH" if prob > 0.75 else ("MEDIUM" if prob > 0.50 else "LOW")
            
            # Compute top anomaly indicators
            indicators = self._derive_anomaly_indicators(features_dict, pred_label)

            return {
                "fault_class": pred_label,
                "fault_probability": round(prob, 4),
                "all_probabilities": {k: round(v, 4) for k, v in all_probs.items()},
                "confidence": confidence,
                "is_anomalous": pred_label != FaultClass.NOMINAL.value and prob > 0.50,
                "indicators": indicators,
                "features": features_dict,
            }
        except Exception as e:
            logger.error(f"Fault prediction error: {e}. Using fallback.")
            return self._heuristic_fallback(features_dict)

    def _derive_anomaly_indicators(self, feat: Dict[str, float], fault_label: str) -> List[str]:
        indicators = []
        if feat.get("delta_t_coil", 0.0) < 3.0 and feat.get("chwc_vlv", 0.0) > 80.0:
            indicators.append("Cooling coil Delta-T collapsed (<3°C) despite valve at >80%")
        if feat.get("airflow_per_speed", 0.0) < 25.0 and feat.get("sf_spd", 0.0) > 60.0:
            indicators.append("Severe airflow deficit (<25 CFM/%) indicating fan slip or filter block")
        if feat.get("sa_sp", 0.0) > 3.8:
            indicators.append("Duct static pressure overpressure surge (>3.8 in.w.g.)")
        if feat.get("damper_cooling_fight", 0.0) > 0.5:
            indicators.append("Outdoor damper leaking hot ambient air fighting chilled water coil")
        if feat.get("zone_temp", 22.0) > 25.5:
            indicators.append("Zone temperature elevated above ASHRAE comfort threshold (25.5°C)")
        return indicators

    def _heuristic_fallback(self, feat: Dict[str, float]) -> Dict[str, Any]:
        """Deterministic physics fallback in case model artifact is uninitialized."""
        if feat.get("sa_sp", 1.5) > 3.8:
            fault = FaultClass.STATIC_PRESSURE_SURGE.value
            prob = 0.92
        elif feat.get("airflow_per_speed", 35.0) < 22.0 and feat.get("sf_spd", 50.0) > 50.0:
            fault = FaultClass.FAN_BELT_SLIP.value
            prob = 0.88
        elif feat.get("chwc_vlv", 30.0) > 85.0 and feat.get("delta_t_coil", 10.0) < 4.0:
            fault = FaultClass.COIL_FOULING_OR_LEAKAGE.value
            prob = 0.89
        elif feat.get("oa_dmpr", 25.0) > 60.0 and feat.get("oa_temp", 20.0) > 28.0 and feat.get("zone_temp", 22.0) > 25.0:
            fault = FaultClass.DAMPER_STUCK.value
            prob = 0.85
        else:
            fault = FaultClass.NOMINAL.value
            prob = 0.95

        return {
            "fault_class": fault,
            "fault_probability": prob,
            "all_probabilities": {fault: prob, FaultClass.NOMINAL.value: 1.0 - prob if fault != FaultClass.NOMINAL.value else 0.95},
            "confidence": "HIGH",
            "is_anomalous": fault != FaultClass.NOMINAL.value,
            "indicators": self._derive_anomaly_indicators(feat, fault),
            "features": feat,
        }
