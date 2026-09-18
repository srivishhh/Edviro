from __future__ import annotations

import os
import glob
import pandas as pd
from backend.ml.features.feature_schema import FaultClass
from backend.ml.inference.fault_predictor import FaultPredictor
from backend.ml.inference.state_predictor import StatePredictor
from backend.ml.training.prepare_dataset import get_scenario_for_filename

DEFAULT_LBNL_DATASET_DIR = os.getenv(
    "LBNL_DATASET_ROOT",
    r"D:\PILOT\LBNL_FDD_Data_Sets_SDAHU\LBNL_FDD_Dataset_SDAHU"
)


def run_real_lbnl_inferences(dataset_dir: str = DEFAULT_LBNL_DATASET_DIR, n_samples_per_scenario: int = 1):
    """
    Pulls actual held-out test rows from different LBNL files and executes end-to-end inference.
    """
    target_files = [
        "AHU_annual.csv",
        "damper_stuck_025_annual.csv",
        "coi_leakage_025_annual.csv",
        "coi_stuck_050_annual.csv",
        "oa_bias_2_annual.csv",
    ]

    fault_predictor = FaultPredictor.get_instance()
    state_predictor = StatePredictor.get_instance()

    print("\n" + "=" * 95)
    print("REAL LBNL DATASET INFERENCE VERIFICATION (HELD-OUT SAMPLES)")
    print("=" * 95)
    print(f"{'ROW':<6} | {'TIMESTAMP':<20} | {'EXPECTED SCENARIO':<20} | {'PREDICTED SCENARIO':<20} | {'CONFIDENCE':<10} | {'PROB':<6}")
    print("-" * 95)

    row_counter = 1
    results = []

    for fname in target_files:
        fpath = os.path.join(dataset_dir, fname)
        if not os.path.exists(fpath):
            continue

        expected_scenario = get_scenario_for_filename(fname)

        # Read sample from the test period (e.g. November/December 2018, row index ~480,000)
        df_sample = pd.read_csv(fpath, skiprows=480000, nrows=10)
        header_df = pd.read_csv(fpath, nrows=1)
        df_sample.columns = header_df.columns

        # Pick active occupied sample
        occupied_subset = df_sample[df_sample["SYS_CTL"] == 1.0]
        sample_row = occupied_subset.iloc[0].to_dict() if len(occupied_subset) > 0 else df_sample.iloc[0].to_dict()

        timestamp = str(sample_row.get("Datetime", "Unknown"))
        pred = fault_predictor.predict(sample_row)

        pred_scenario = pred["fault_class"]
        confidence = pred["confidence"]
        prob = pred["fault_probability"]

        print(f"{row_counter:<6} | {timestamp:<20} | {expected_scenario:<20} | {pred_scenario:<20} | {confidence:<10} | {prob:<6.2f}")
        
        # Also run state prediction
        cf_res = state_predictor.predict_counterfactual(sample_row, {"chwc_vlv": 45.0, "sf_spd": 75.0})

        results.append({
            "row": row_counter,
            "timestamp": timestamp,
            "file": fname,
            "expected_scenario": expected_scenario,
            "predicted_scenario": pred_scenario,
            "confidence": confidence,
            "probability": prob,
            "counterfactual_deltas": cf_res["deltas"],
        })
        row_counter += 1

    print("=" * 95 + "\n")
    return results


if __name__ == "__main__":
    run_real_lbnl_inferences()
