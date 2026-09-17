from __future__ import annotations

import os
import json
import logging
from typing import Dict, Any, Tuple, List
import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from backend.ml.training.prepare_dataset import load_and_prepare_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")

STATE_CF_INPUT_FEATURES: List[str] = [
    "oa_temp",
    "ra_temp",
    "ma_temp",
    "sa_temp",
    "zone_temp",
    "sa_cfm",
    "sa_sp",
    "power",
    "oa_dmpr",
    "chwc_vlv",
    "hw_vlv",
    "sf_spd",
]

STATE_CF_TARGET_CHANNELS: List[str] = [
    "zone_temp",
    "sa_temp",
    "sa_cfm",
    "power",
]


def train_counterfactual_state_models(
    artifacts_dir: str = ARTIFACTS_DIR,
) -> Tuple[Dict[str, HistGradientBoostingRegressor], Dict[str, Any]]:
    """
    Trains regressors for predicting counterfactual outcome states given state + interventions.
    """
    os.makedirs(artifacts_dir, exist_ok=True)
    
    logger.info("Loading dataset for Counterfactual State Regressors...")
    _, _, X_state, y_state = load_and_prepare_dataset()
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_state, y_state, test_size=0.20, random_state=42
    )
    
    models: Dict[str, HistGradientBoostingRegressor] = {}
    metrics: Dict[str, Dict[str, float]] = {}
    
    for idx, target_name in enumerate(STATE_CF_TARGET_CHANNELS):
        logger.info(f"Training Regressor for target: '{target_name}'...")
        y_train_col = y_train[:, idx]
        y_test_col = y_test[:, idx]
        
        reg = HistGradientBoostingRegressor(
            max_iter=150,
            learning_rate=0.08,
            max_leaf_nodes=31,
            min_samples_leaf=20,
            random_state=42,
        )
        reg.fit(X_train, y_train_col)
        
        y_pred = reg.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test_col, y_pred)))
        mae = float(mean_absolute_error(y_test_col, y_pred))
        r2 = float(r2_score(y_test_col, y_pred))
        
        logger.info(f"Target '{target_name}' -> RMSE: {rmse:.4f}, MAE: {mae:.4f}, R2: {r2:.4f}")
        
        models[target_name] = reg
        metrics[target_name] = {
            "rmse": rmse,
            "mae": mae,
            "r2": r2,
        }
        
    # Save Model Artifacts
    model_path = os.path.join(artifacts_dir, "state_regressors.joblib")
    joblib.dump(models, model_path)
    logger.info(f"Saved state regressors to: {model_path}")
    
    # Save Metadata
    metadata = {
        "model_type": "HistGradientBoostingRegressor_MultiTarget",
        "input_features": STATE_CF_INPUT_FEATURES,
        "target_channels": STATE_CF_TARGET_CHANNELS,
        "metrics": metrics,
    }
    
    meta_path = os.path.join(artifacts_dir, "state_regressors_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved state model metadata to: {meta_path}")
    
    return models, metadata


if __name__ == "__main__":
    train_counterfactual_state_models()
