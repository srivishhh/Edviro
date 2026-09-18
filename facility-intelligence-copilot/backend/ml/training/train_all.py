from __future__ import annotations

import os
import sys
import json
import subprocess
import logging
from datetime import datetime, timezone
from typing import Dict, Any

import sklearn
import lightgbm

from backend.ml.training.prepare_dataset import load_and_prepare_lbnl_dataset
from backend.ml.training.train_fault_model import train_fault_classifier
from backend.ml.training.train_state_model import train_counterfactual_state_models

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")


def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "unknown"


def train_and_save_all(sample_step: int = 5) -> Dict[str, Any]:
    """
    Master pipeline: Ingests LBNL dataset, trains fault classifier and state regressors,
    and produces consolidated backend/ml/artifacts/model_metadata.json.
    """
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    logger.info("=" * 70)
    logger.info("STARTING GSENSE 3.0 ML RE-TRAINING & VALIDATION HARDENING")
    logger.info("=" * 70)

    # 1. Dataset Ingestion with Chronological Split
    split = load_and_prepare_lbnl_dataset(sample_step=sample_step)

    # 2. Train Fault Classifier
    clf, fault_meta = train_fault_classifier(dataset_split=split, artifacts_dir=ARTIFACTS_DIR)

    # 3. Train Counterfactual State Regressors
    regs, state_meta = train_counterfactual_state_models(dataset_split=split, artifacts_dir=ARTIFACTS_DIR)

    # 4. Consolidated Model Metadata
    master_metadata = {
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit(),
        "environment": {
            "python_version": sys.version.split()[0],
            "scikit_learn_version": sklearn.__version__,
            "lightgbm_version": lightgbm.__version__,
        },
        "dataset_files": split.metadata.get("dataset_files", []),
        "split_strategy": split.metadata.get("split_strategy", "chronological_70_15_15"),
        "date_ranges": split.metadata.get("date_ranges", {}),
        "row_counts": {
            "total_sampled_rows": split.metadata.get("total_rows", 0),
            "train_rows": split.metadata.get("train_rows", 0),
            "validation_rows": split.metadata.get("validation_rows", 0),
            "test_rows": split.metadata.get("test_rows", 0),
        },
        "class_distribution": split.metadata.get("class_distribution", {}),
        "models": {
            "fault_classifier": {
                "artifact": "fault_classifier.joblib",
                "model_type": fault_meta["model_type"],
                "feature_count": fault_meta["feature_count"],
                "feature_names": fault_meta["feature_names"],
                "classes": fault_meta["classes"],
                "class_mapping": fault_meta["class_mapping"],
                "test_metrics": fault_meta["metrics"],
                "classification_report": fault_meta["classification_report"],
                "confusion_matrix": fault_meta["confusion_matrix"],
            },
            "state_regressors": {
                "artifact": "state_regressors.joblib",
                "model_type": state_meta["model_type"],
                "input_feature_count": state_meta["input_feature_count"],
                "input_features": state_meta["input_features"],
                "targets": state_meta["target_channels"],
                "per_target_test_metrics": state_meta["test_metrics"],
                "aggregate_test_metrics": state_meta["aggregate_metrics"],
            },
        },
    }

    meta_path = os.path.join(ARTIFACTS_DIR, "model_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(master_metadata, f, indent=2)
    logger.info(f"Successfully serialized consolidated metadata to: {meta_path}")
    logger.info("=" * 70)
    logger.info("GSENSE 3.0 ML HARDENING & TRAINING COMPLETE")
    logger.info("=" * 70)

    return master_metadata


if __name__ == "__main__":
    train_and_save_all()
