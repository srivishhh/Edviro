from __future__ import annotations

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

from backend.ml.features.feature_schema import (
    ALL_FAULT_FEATURES,
    FAULT_INT_TO_LABEL,
    FAULT_LABEL_TO_INT,
)
from backend.ml.training.prepare_dataset import load_and_prepare_lbnl_dataset, DatasetSplit

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")


def train_fault_classifier(
    dataset_split: DatasetSplit | None = None,
    artifacts_dir: str = ARTIFACTS_DIR,
) -> Tuple[HistGradientBoostingClassifier, Dict[str, Any]]:
    """
    Trains, validates, and strictly evaluates the HVAC Fault Classifier using chronological splits.
    """
    os.makedirs(artifacts_dir, exist_ok=True)
    
    if dataset_split is None:
        logger.info("Loading LBNL dataset with chronological 70/15/15 split...")
        dataset_split = load_and_prepare_lbnl_dataset()

    X_train, y_train = dataset_split.X_train_fault, dataset_split.y_train_fault
    X_val, y_val = dataset_split.X_val_fault, dataset_split.y_val_fault
    X_test, y_test = dataset_split.X_test_fault, dataset_split.y_test_fault

    logger.info(f"Training Fault Classifier on {len(X_train)} samples across {X_train.shape[1]} features...")

    # Calculate baseline majority class accuracy on test set
    unique_test, counts_test = np.unique(y_test, return_counts=True)
    majority_count = counts_test.max()
    baseline_majority_accuracy = float(majority_count / len(y_test))

    clf = HistGradientBoostingClassifier(
        max_iter=150,
        learning_rate=0.08,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        random_state=42,
        class_weight="balanced",
    )

    clf.fit(X_train, y_train)

    # Validate on validation split
    val_pred = clf.predict(X_val)
    val_acc = float(accuracy_score(y_val, val_pred))
    val_f1 = float(f1_score(y_val, val_pred, average="macro"))
    logger.info(f"Validation Set -> Accuracy: {val_acc:.4f}, Macro F1: {val_f1:.4f}")

    # Primary Evaluation on Held-out Chronological Test Set
    test_pred = clf.predict(X_test)
    test_acc = float(accuracy_score(y_test, test_pred))
    test_macro_prec = float(precision_score(y_test, test_pred, average="macro", zero_division=0))
    test_macro_rec = float(recall_score(y_test, test_pred, average="macro", zero_division=0))
    test_macro_f1 = float(f1_score(y_test, test_pred, average="macro", zero_division=0))

    # Per-class metrics
    target_names = [FAULT_INT_TO_LABEL[i] for i in range(len(FAULT_INT_TO_LABEL))]
    class_report = classification_report(
        y_test, test_pred, target_names=target_names, output_dict=True, zero_division=0
    )

    # Confusion matrix
    conf_matrix = confusion_matrix(y_test, test_pred).tolist()

    logger.info("=" * 60)
    logger.info("FAULT CLASSIFIER - HELD-OUT TEST SET EVALUATION")
    logger.info(f"Baseline Majority Accuracy: {baseline_majority_accuracy:.4f}")
    logger.info(f"Test Set Accuracy:          {test_acc:.4f}")
    logger.info(f"Macro Precision:            {test_macro_prec:.4f}")
    logger.info(f"Macro Recall:               {test_macro_rec:.4f}")
    logger.info(f"Macro F1 Score:             {test_macro_f1:.4f}")
    logger.info("Confusion Matrix:")
    for row in conf_matrix:
        logger.info(f"  {row}")
    logger.info("=" * 60)

    # Save Model Artifact
    model_path = os.path.join(artifacts_dir, "fault_classifier.joblib")
    joblib.dump(clf, model_path)
    logger.info(f"Saved fault model artifact to: {model_path}")

    # Save Model Metadata
    metadata: Dict[str, Any] = {
        "model_name": "fault_classifier",
        "model_type": "HistGradientBoostingClassifier",
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "feature_names": ALL_FAULT_FEATURES,
        "feature_count": len(ALL_FAULT_FEATURES),
        "class_mapping": FAULT_LABEL_TO_INT,
        "classes": target_names,
        "split_strategy": dataset_split.metadata.get("split_strategy", "chronological"),
        "train_rows": len(X_train),
        "validation_rows": len(X_val),
        "test_rows": len(X_test),
        "metrics": {
            "baseline_majority_accuracy": round(baseline_majority_accuracy, 4),
            "test_accuracy": round(test_acc, 4),
            "macro_precision": round(test_macro_prec, 4),
            "macro_recall": round(test_macro_rec, 4),
            "macro_f1": round(test_macro_f1, 4),
            "validation_accuracy": round(val_acc, 4),
            "validation_macro_f1": round(val_f1, 4),
        },
        "classification_report": class_report,
        "confusion_matrix": conf_matrix,
        "dataset_files": dataset_split.metadata.get("dataset_files", []),
    }

    meta_path = os.path.join(artifacts_dir, "fault_classifier_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved fault model metadata to: {meta_path}")

    return clf, metadata


if __name__ == "__main__":
    train_fault_classifier()
