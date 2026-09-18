import os
import joblib
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "backend", "ml", "artifacts")

print(f"Checking models in: {MODELS_DIR}")

# List files in MODELS_DIR
if os.path.exists(MODELS_DIR):
    print("Files in artifacts dir:", os.listdir(MODELS_DIR))

# 1. Fault Classifier
classifier_path = os.path.join(MODELS_DIR, "fault_classifier.joblib")
if os.path.exists(classifier_path):
    clf_data = joblib.load(classifier_path)
    print("\n--- FAULT CLASSIFIER INFO ---")
    if isinstance(clf_data, dict):
        print("Keys:", list(clf_data.keys()))
        for k in clf_data:
            val = clf_data[k]
            if hasattr(val, "shape"):
                print(f"  {k}: shape {val.shape}")
            elif isinstance(val, (list, dict, tuple)):
                print(f"  {k}: len {len(val)} -> {val[:5] if isinstance(val, list) else val}")
            else:
                print(f"  {k}: {type(val)}")
    else:
        print("Loaded object type:", type(clf_data))
        if hasattr(clf_data, "classes_"):
            print("Classes:", clf_data.classes_)
        if hasattr(clf_data, "n_features_in_"):
            print("Number of features:", clf_data.n_features_in_)
        if hasattr(clf_data, "feature_names_in_"):
            print("Feature names in model:", clf_data.feature_names_in_)
else:
    print(f"FAULT CLASSIFIER NOT FOUND AT {classifier_path}")

# 2. State Regressors
regressor_path = os.path.join(MODELS_DIR, "state_regressors.joblib")
if os.path.exists(regressor_path):
    reg_data = joblib.load(regressor_path)
    print("\n--- STATE REGRESSORS INFO ---")
    if isinstance(reg_data, dict):
        print("Keys:", list(reg_data.keys()))
        for k, v in reg_data.items():
            print(f"  {k}: {type(v)}")
    else:
        print("Loaded object type:", type(reg_data))

# 3. State Regressors Meta
meta_path = os.path.join(MODELS_DIR, "state_regressors_meta.json")
if not os.path.exists(meta_path):
    meta_path = os.path.join(MODELS_DIR, "metadata.json")
if os.path.exists(meta_path):
    with open(meta_path, "r") as f:
        meta = json.load(f)
    print(f"\n--- META INFO ({os.path.basename(meta_path)}) ---")
    print(json.dumps(meta, indent=2))
else:
    print(f"META NOT FOUND AT {meta_path}")
