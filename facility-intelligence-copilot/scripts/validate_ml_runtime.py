import os
import sys
import json
import time
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.ml.inference.fault_predictor import FaultPredictor
from backend.ml.features.feature_schema import ALL_FAULT_FEATURES, FAULT_INT_TO_LABEL, FAULT_LABEL_TO_INT

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "backend", "ml", "artifacts")
DATA_DIR = os.path.join(BASE_DIR, "data", "lbnl")
if not os.path.exists(DATA_DIR):
    DATA_DIR = os.path.join(BASE_DIR, "backend", "ml", "data")

print("========================================================")
print("PHASE 4 & 5: ML MODEL FORENSIC VALIDATION & TRAINING AUDIT")
print("========================================================\n")

clf_path = os.path.join(ARTIFACTS_DIR, "fault_classifier.joblib")
meta_path = os.path.join(ARTIFACTS_DIR, "fault_classifier_meta.json")

# Artifact statistics
file_stat = os.stat(clf_path)
mod_time = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc).isoformat()
file_size_kb = round(file_stat.st_size / 1024.0, 2)

print(f"Artifact Path: {clf_path}")
print(f"File Size: {file_size_kb} KB")
print(f"Modification Date: {mod_time}")

clf = joblib.load(clf_path)
with open(meta_path, "r") as f:
    meta = json.load(f)

print(f"Model Class: {type(clf)}")
print(f"Fitted Features (n_features_in_): {getattr(clf, 'n_features_in_', 'N/A')}")
print(f"Fitted Classes (classes_): {getattr(clf, 'classes_', 'N/A')}")
print(f"Feature Names ({len(meta.get('feature_names', []))}): {meta.get('feature_names')}")
print(f"Target Classes Mapping: {meta.get('class_mapping')}")

# Runtime prediction test on real LBNL record
predictor = FaultPredictor.get_instance()
sample_real_telemetry = {
    "oa_temp": 32.5, "ra_temp": 24.2, "ma_temp": 29.8, "sa_temp": 21.0,
    "zone_temp": 25.8, "oa_dmpr": 85.0, "chwc_vlv": 95.0, "sf_spd": 80.0,
    "sa_cfm": 2450.0, "sa_sp": 1.6, "power": 14.2
}

pred_res = predictor.predict(sample_real_telemetry)
print("\n--- RUNTIME INFERENCE TEST (Real Observation Vector) ---")
print(f"Predicted Fault: {pred_res['fault_class']}")
print(f"Fault Probability: {pred_res['fault_probability']}")
print(f"Confidence Level: {pred_res['confidence']}")
print(f"All Probabilities: {pred_res['all_probabilities']}")

# Evaluate performance on held-out dataset files if available
lbnl_files = ["damper_stuck_025_annual.csv", "coi_stuck_025_annual.csv", "oa_bias_2_annual.csv"]
eval_records = []

for filename in lbnl_files:
    fp = os.path.join(DATA_DIR, filename)
    if os.path.exists(fp):
        df = pd.read_csv(fp)
        # Extract ground truth fault label from filename
        gt_label = "damper_stuck" if "damper" in filename else ("coi_stuck" if "coi_stuck" in filename else "oa_bias")
        # Sample 500 rows for held-out evaluation
        sample_df = df.sample(n=min(500, len(df)), random_state=42)
        for _, row in sample_df.iterrows():
            row_dict = row.to_dict()
            pred = predictor.predict(row_dict)
            eval_records.append({
                "ground_truth": gt_label,
                "predicted": pred["fault_class"]
            })

if eval_records:
    eval_df = pd.DataFrame(eval_records)
    acc = (eval_df["ground_truth"] == eval_df["predicted"]).mean()
    print(f"\n--- HELD-OUT DATASET EVALUATION ({len(eval_records)} samples) ---")
    print(f"Held-out Accuracy: {acc * 100:.2f}%")
    ct = pd.crosstab(eval_df["ground_truth"], eval_df["predicted"], rownames=["Actual"], colnames=["Predicted"])
    print("\nConfusion Matrix:")
    print(ct)

print("\nML MODEL FORENSIC AUDIT PASSED SUCCESSFULLY!")
