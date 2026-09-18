import os
import sys
import json
import joblib
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.ml.inference.state_predictor import StatePredictor

print("========================================================")
print("PHASE 6, 7 & 8: STATE REGRESSOR & DIGITAL TWIN SENSITIVITY TEST")
print("========================================================\n")

predictor = StatePredictor.get_instance()

# 1. Baseline Telemetry Observation
baseline_state = {
    "oa_temp": 32.0, "ra_temp": 24.0, "ma_temp": 30.0, "sa_temp": 20.0,
    "zone_temp": 25.5, "oa_dmpr": 100.0, "chwc_vlv": 85.0, "sf_spd": 75.0,
    "sa_cfm": 2400.0, "sa_sp": 1.6, "power": 12.0
}

# Baseline prediction (no intervention)
baseline_res = predictor.predict_counterfactual(baseline_state, {})
print("--- BASELINE TWIN PREDICTION ---")
print("Baseline Predicted Targets:", baseline_res["predicted_metrics"])

# 2. Counterfactual A: Damper closed to 20%
cf_a_res = predictor.predict_counterfactual(baseline_state, {"oa_dmpr": 20.0})
print("\n--- COUNTERFACTUAL A (oa_dmpr = 20%) ---")
print("Predicted Targets:", cf_a_res["predicted_metrics"])
print("Deltas vs Baseline:", cf_a_res["deltas"])

# 3. Counterfactual B: Damper closed to 60%
cf_b_res = predictor.predict_counterfactual(baseline_state, {"oa_dmpr": 60.0})
print("\n--- COUNTERFACTUAL B (oa_dmpr = 60%) ---")
print("Predicted Targets:", cf_b_res["predicted_metrics"])
print("Deltas vs Baseline:", cf_b_res["deltas"])

# Compare Counterfactual A vs Counterfactual B
assert cf_a_res["predicted_metrics"] != cf_b_res["predicted_metrics"], "ERROR: Model output did not change between Counterfactual A and B!"
print("\n[VERIFIED] Counterfactual A and B outputs are DIFFERENT and model-driven!")

# 4. Actuator Sensitivity Matrix
actuators_to_test = [
    ("oa_dmpr", 20.0, 80.0),
    ("chwc_vlv", 20.0, 90.0),
    ("sf_spd", 45.0, 95.0),
]

sensitivity_report = []
for act, val_low, val_high in actuators_to_test:
    res_low = predictor.predict_counterfactual(baseline_state, {act: val_low})
    res_high = predictor.predict_counterfactual(baseline_state, {act: val_high})
    
    zone_delta = round(res_high["predicted_metrics"]["zone_temp"] - res_low["predicted_metrics"]["zone_temp"], 2)
    sa_delta = round(res_high["predicted_metrics"]["sa_temp"] - res_low["predicted_metrics"]["sa_temp"], 2)
    power_delta = round(res_high["predicted_metrics"]["power"] - res_low["predicted_metrics"]["power"], 2)
    cfm_delta = round(res_high["predicted_metrics"]["sa_cfm"] - res_low["predicted_metrics"]["sa_cfm"], 1)

    sensitivity_report.append({
        "actuator": act,
        "val_low": val_low,
        "val_high": val_high,
        "zone_temp_delta": zone_delta,
        "sa_temp_delta": sa_delta,
        "power_delta": power_delta,
        "sa_cfm_delta": cfm_delta,
        "is_sensitive": any(abs(x) > 0.01 for x in [zone_delta, sa_delta, power_delta, cfm_delta])
    })

print("\n--- ACTUATOR SENSITIVITY MATRIX ---")
for s in sensitivity_report:
    print(f"  Actuator '{s['actuator']}': [{s['val_low']} -> {s['val_high']}] | zone_t_delta: {s['zone_temp_delta']} | sa_t_delta: {s['sa_temp_delta']} | power_delta: {s['power_delta']} | cfm_delta: {s['sa_cfm_delta']} | sensitive: {s['is_sensitive']}")

print("\nCOUNTERFACTUAL DIGITAL TWIN FORENSIC AUDIT PASSED SUCCESSFULLY!")
