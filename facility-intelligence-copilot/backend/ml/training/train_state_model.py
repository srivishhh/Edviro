from __future__ import annotations

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, List
import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from backend.ml.features.feature_schema import (
    STATE_REGRESSOR_INPUT_FEATURES,
    STATE_REGRESSOR_TARGETS,
)
from backend.ml.training.prepare_dataset import load_and_prepare_lbnl_dataset, DatasetSplit

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")


def train_counterfactual_state_models(
    dataset_split: DatasetSplit | None = None,
    artifacts_dir: str = ARTIFACTS_DIR,
) -> Tuple[Dict[str, HistGradientBoostingRegressor], Dict[str, Any]]:
    """
    Trains, validates, and evaluates the Counterfactual State Regressors using chronological splits.
    """
    os.makedirs(artifacts_dir, exist_ok=True)

    if dataset_split is None:
        logger.info("Loading LBNL dataset with chronological split for State Regressors...")
        dataset_split = load_and_prepare_lbnl_dataset()

    X_train, y_train = dataset_split.X_train_state, dataset_split.y_train_state
    X_val, y_val = dataset_split.X_val_state, dataset_split.y_val_state
    X_test, y_test = dataset_split.X_test_state, dataset_split.y_test_state

    logger.info(f"Training State Regressors on {len(X_train)} samples across {X_train.shape[1]} inputs...")

    models: Dict[str, HistGradientBoostingRegressor] = {}
    test_metrics: Dict[str, Dict[str, float]] = {}
    val_metrics: Dict[str, Dict[str, float]] = {}

    r2_scores_list = []
    mae_scores_list = []
    rmse_scores_list = []

    for idx, target_name in enumerate(STATE_REGRESSOR_TARGETS):
        logger.info(f"Fitting Regressor for target: '{target_name}'...")
        y_train_col = y_train[:, idx]
        y_val_col = y_val[:, idx]
        y_test_col = y_test[:, idx]

        reg = HistGradientBoostingRegressor(
            max_iter=150,
            learning_rate=0.08,
            max_leaf_nodes=31,
            min_samples_leaf=20,
            random_state=42,
        )
        reg.fit(X_train, y_train_col)

        # Validation evaluation
        y_val_pred = reg.predict(X_val)
        val_rmse = float(np.sqrt(mean_squared_error(y_val_col, y_val_pred)))
        val_mae = float(mean_absolute_error(y_val_col, y_val_pred))
        val_r2 = float(r2_score(y_val_col, y_val_pred))
        val_metrics[target_name] = {"rmse": round(val_rmse, 4), "mae": round(val_mae, 4), "r2": round(val_r2, 4)}

        # Held-out Chronological Test evaluation
        y_test_pred = reg.predict(X_test)
        test_rmse = float(np.sqrt(mean_squared_error(y_test_col, y_test_pred)))
        test_mae = float(mean_absolute_error(y_test_col, y_test_pred))
        test_r2 = float(r2_score(y_test_col, y_test_pred))
        test_metrics[target_name] = {"rmse": round(test_rmse, 4), "mae": round(test_mae, 4), "r2": round(test_r2, 4)}

        r2_scores_list.append(test_r2)
        mae_scores_list.append(test_mae)
        rmse_scores_list.append(test_rmse)

        models[target_name] = reg
        logger.info(f"Target '{target_name}' (Test Set) -> RMSE: {test_rmse:.4f}, MAE: {test_mae:.4f}, R2: {test_r2:.4f}")

    aggregate_test_r2 = float(np.mean(r2_scores_list))
    aggregate_test_mae = float(np.mean(mae_scores_list))
    aggregate_test_rmse = float(np.mean(rmse_scores_list))

    logger.info("=" * 60)
    logger.info("STATE REGRESSORS - HELD-OUT TEST SET EVALUATION")
    logger.info(f"Mean Test R2:   {aggregate_test_r2:.4f}")
    logger.info(f"Mean Test MAE:  {aggregate_test_mae:.4f}")
    logger.info(f"Mean Test RMSE: {aggregate_test_rmse:.4f}")
    logger.info("Per-Target Breakdown:")
    for tgt, met in test_metrics.items():
        logger.info(f"  {tgt:<12} -> R2: {met['r2']:.4f}, MAE: {met['mae']:.4f}, RMSE: {met['rmse']:.4f}")
    logger.info("=" * 60)

    # Save Model Artifacts
    model_path = os.path.join(artifacts_dir, "state_regressors.joblib")
    joblib.dump(models, model_path)
    logger.info(f"Saved state regressors artifact to: {model_path}")

    # Save Model Metadata
    metadata: Dict[str, Any] = {
        "model_name": "state_regressors",
        "model_type": "HistGradientBoostingRegressor_MultiTarget",
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "input_features": STATE_REGRESSOR_INPUT_FEATURES,
        "input_feature_count": len(STATE_REGRESSOR_INPUT_FEATURES),
        "target_channels": STATE_REGRESSOR_TARGETS,
        "split_strategy": dataset_split.metadata.get("split_strategy", "chronological"),
        "train_rows": len(X_train),
        "validation_rows": len(X_val),
        "test_rows": len(X_test),
        "test_metrics": test_metrics,
        "validation_metrics": val_metrics,
        "aggregate_metrics": {
            "mean_test_r2": round(aggregate_test_r2, 4),
            "mean_test_mae": round(aggregate_test_mae, 4),
            "mean_test_rmse": round(aggregate_test_rmse, 4),
        },
        "dataset_files": dataset_split.metadata.get("dataset_files", []),
    }

    meta_path = os.path.join(artifacts_dir, "state_regressors_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved state model metadata to: {meta_path}")

    return models, metadata


if __name__ == "__main__":
    train_counterfactual_state_models()
