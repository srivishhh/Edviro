from __future__ import annotations

import os
import json
import logging
from typing import Dict, Any, Tuple
import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from backend.ml.features.feature_schema import (
    ALL_FAULT_FEATURES,
    FAULT_INT_TO_LABEL,
    FAULT_LABEL_TO_INT,
)
from backend.ml.training.prepare_dataset import load_and_prepare_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")


def train_fault_classifier(
    artifacts_dir: str = ARTIFACTS_DIR,
    n_samples: int = 40000,
) -> Tuple[Any, Dict[str, Any]]:
    """
    Trains and saves the Fault Classification Model.
    """
    os.makedirs(artifacts_dir, exist_ok=True)
    
    logger.info("Loading training data for Fault Classification...")
    X_fault, y_fault, _, _ = load_and_prepare_dataset()
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_fault, y_fault, test_size=0.20, random_state=42, stratify=y_fault
    )
    
    logger.info(f"Training set size: {X_train.shape[0]}, Test set size: {X_test.shape[0]}")
    
    # Train high-performance gradient boosting classifier
    clf = HistGradientBoostingClassifier(
        max_iter=150,
        learning_rate=0.08,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        random_state=42,
        class_weight="balanced",
    )
    
    logger.info("Fitting HistGradientBoostingClassifier...")
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)
    
    acc = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro"))
    
    logger.info(f"Fault Model Evaluation - Accuracy: {acc:.4f}, Macro F1: {macro_f1:.4f}")
    
    target_names = [FAULT_INT_TO_LABEL[i] for i in range(len(FAULT_INT_TO_LABEL))]
    report = classification_report(y_test, y_pred, target_names=target_names, output_dict=True)
    
    # Save Model Artifact
    model_path = os.path.join(artifacts_dir, "fault_classifier.joblib")
    joblib.dump(clf, model_path)
    logger.info(f"Saved fault model to: {model_path}")
    
    # Save Metadata
    metadata = {
        "model_type": "HistGradientBoostingClassifier",
        "feature_names": ALL_FAULT_FEATURES,
        "class_mapping": FAULT_LABEL_TO_INT,
        "accuracy": acc,
        "macro_f1": macro_f1,
        "classification_report": report,
    }
    
    meta_path = os.path.join(artifacts_dir, "fault_classifier_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved fault model metadata to: {meta_path}")
    
    return clf, metadata


if __name__ == "__main__":
    train_fault_classifier()
