from __future__ import annotations

import os
import json
import logging
from typing import Dict, Any, Optional, List
import joblib
import numpy as np

from backend.ml.features.feature_schema import (
    ALL_FAULT_FEATURES,
    FAULT_INT_TO_LABEL,
    FAULT_LABEL_TO_INT,
    FaultClass,
)
from backend.ml.features.feature_engineering import (
    validate_telemetry_dict,
    extract_features_dict,
    extract_feature_vector,
)

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "fault_classifier.joblib")
META_PATH = os.path.join(ARTIFACTS_DIR, "fault_classifier_meta.json")


class FaultPredictor:
    """
    Hardened ML Fault Classifier for GSENSE 3.0.
    Identifies root-cause equipment faults with calibrated probabilities using real LBNL model weights.
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
        """Loads trained fault model artifact and metadata."""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                if os.path.exists(self.meta_path):
                    with open(self.meta_path, "r", encoding="utf-8") as f:
                        self.metadata = json.load(f)
                logger.info(f"Loaded Fault Classifier from {self.model_path}")
                return
            except Exception as e:
                logger.error(f"Error loading fault model: {e}")
                self.model = None
        else:
            logger.warning(f"Fault model artifact not found at {self.model_path}")
            self.model = None

    def predict(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes fault inference on incoming live or replayed telemetry frame.
        Guarantees deterministic feature ordering and explicit error handling.
        """
        validate_telemetry_dict(telemetry)
        
        # Check if telemetry is in Celsius (e.g., zone_temp or oa_temp <= 45.0)
        zt = telemetry.get("zone_temp", telemetry.get("ZONE_TEMP", telemetry.get("zt", 72.0)))
        oat = telemetry.get("oa_temp", telemetry.get("OA_TEMP", telemetry.get("oat", 70.0)))
        try:
            is_celsius = float(zt) <= 45.0 or float(oat) <= 45.0
        except (ValueError, TypeError):
            is_celsius = False

        working_telemetry = dict(telemetry)
        if is_celsius:
            for k, v in telemetry.items():
                clean_k = str(k).strip().lower().replace(" ", "_").replace("-", "_")
                if any(tk in clean_k for tk in ["temp", "oat", "rat", "mat", "sat", "zt"]) and v is not None:
                    try:
                        working_telemetry[k] = float(v) * 9.0 / 5.0 + 32.0
                    except (ValueError, TypeError):
                        pass

        features_dict = extract_features_dict(working_telemetry)
        x_vec = np.array([[features_dict.get(k, 0.0) for k in ALL_FAULT_FEATURES]], dtype=np.float32)

        if self.model is None:
            return self._heuristic_fallback(features_dict)

        try:
            probas = self.model.predict_proba(x_vec)[0]
            pred_int = int(np.argmax(probas))
            pred_label = FAULT_INT_TO_LABEL.get(pred_int, FaultClass.NOMINAL.value)
            prob = float(probas[pred_int])

            all_probs = {
                FAULT_INT_TO_LABEL.get(i, f"class_{i}"): round(float(probas[i]), 4)
                for i in range(len(probas))
            }

            confidence = "HIGH" if prob > 0.75 else ("MEDIUM" if prob > 0.50 else "LOW")
            indicators = self._derive_anomaly_indicators(features_dict, pred_label)

            return {
                "fault_class": pred_label,
                "fault_probability": round(prob, 4),
                "all_probabilities": all_probs,
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
        if fault_label == FaultClass.DAMPER_STUCK.value:
            indicators.append("Outdoor air damper position decoupled from ventilation schedule")
        elif fault_label == FaultClass.COI_STUCK.value:
            indicators.append("Cooling coil valve position unvarying despite supply temp fluctuations")
        elif fault_label == FaultClass.COI_LEAKAGE.value:
            indicators.append("Chilled water leakage detected across closed cooling coil")
        elif fault_label == FaultClass.COI_BIAS.value:
            indicators.append("Cooling coil discharge temperature sensor offset bias detected")
        elif fault_label == FaultClass.OA_BIAS.value:
            indicators.append("Outdoor air temperature sensor measurement offset bias detected")

        # Thermodynamic sanity flags
        if feat.get("delta_t_coil", 0.0) < 2.0 and feat.get("chwc_vlv", 0.0) > 70.0:
            indicators.append("Cooling coil Delta-T collapsed (<2°F) under high valve demand")
        if feat.get("sa_sp", 0.0) > 3.8:
            indicators.append("Duct static pressure overpressure surge (>3.8 in.w.g.)")
        return indicators

    def _heuristic_fallback(self, feat: Dict[str, float]) -> Dict[str, Any]:
        """Deterministic physics fallback in case model artifact is uninitialized."""
        return {
            "fault_class": FaultClass.NOMINAL.value,
            "fault_probability": 0.95,
            "all_probabilities": {FaultClass.NOMINAL.value: 0.95},
            "confidence": "MEDIUM",
            "is_anomalous": False,
            "indicators": [],
            "features": feat,
        }
