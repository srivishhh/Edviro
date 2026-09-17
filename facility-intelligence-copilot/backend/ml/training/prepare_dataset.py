from __future__ import annotations

import os
import glob
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

from backend.ml.features.feature_schema import (
    FaultClass,
    FAULT_LABEL_TO_INT,
    FAULT_INT_TO_LABEL,
    FILENAME_SCENARIO_MAP,
    ALL_FAULT_FEATURES,
    STATE_REGRESSOR_INPUT_FEATURES,
    STATE_REGRESSOR_TARGETS,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_LBNL_DATASET_DIR = os.getenv(
    "LBNL_DATASET_ROOT",
    r"D:\PILOT\LBNL_FDD_Data_Sets_SDAHU\LBNL_FDD_Dataset_SDAHU"
)


@dataclass
class DatasetSplit:
    # Fault Classification matrices
    X_train_fault: np.ndarray
    y_train_fault: np.ndarray
    X_val_fault: np.ndarray
    y_val_fault: np.ndarray
    X_test_fault: np.ndarray
    y_test_fault: np.ndarray

    # Counterfactual State Regression matrices
    X_train_state: np.ndarray
    y_train_state: np.ndarray
    X_val_state: np.ndarray
    y_val_state: np.ndarray
    X_test_state: np.ndarray
    y_test_state: np.ndarray

    # Dataset Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


def get_scenario_for_filename(filename: str) -> str:
    """Matches LBNL filename to ground truth scenario taxonomy."""
    base = os.path.basename(filename).replace(".csv", "")
    for key, label in FILENAME_SCENARIO_MAP.items():
        if key in base:
            return label
    return FaultClass.NOMINAL.value


def extract_features_dataframe_vectorized(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    High-speed vectorized extraction of ALL_FAULT_FEATURES and STATE_REGRESSOR_INPUT/OUTPUT matrices.
    Returns:
        X_fault_matrix: (N, 21) matching ALL_FAULT_FEATURES
        X_state_matrix: (N, 12) matching STATE_REGRESSOR_INPUT_FEATURES
        y_state_matrix: (N, 4)  matching STATE_REGRESSOR_TARGETS
    """
    n = len(df)
    
    # 1. Base telemetry extraction
    oa_temp = df["OA_TEMP"].values.astype(np.float32)
    ra_temp = df["RA_TEMP"].values.astype(np.float32)
    ma_temp = df["MA_TEMP"].values.astype(np.float32)
    sa_temp = df["SA_TEMP"].values.astype(np.float32)

    # Multi-zone average
    zone_cols = [f"ZONE_TEMP_{i}" for i in range(1, 6) if f"ZONE_TEMP_{i}" in df.columns]
    if zone_cols:
        zone_temp = df[zone_cols].mean(axis=1).values.astype(np.float32)
    else:
        zone_temp = ra_temp.copy()

    # Normalize actuator scales (fractions 0-1 to 0-100%)
    oa_dmpr_raw = df["OA_DMPR"].values.astype(np.float32)
    oa_dmpr = np.where(oa_dmpr_raw <= 1.0, oa_dmpr_raw * 100.0, oa_dmpr_raw)

    ra_dmpr_raw = df["RA_DMPR"].values.astype(np.float32)
    ra_dmpr = np.where(ra_dmpr_raw <= 1.0, ra_dmpr_raw * 100.0, ra_dmpr_raw)

    chwc_vlv_raw = df["CHWC_VLV"].values.astype(np.float32)
    chwc_vlv = np.where(chwc_vlv_raw <= 1.0, chwc_vlv_raw * 100.0, chwc_vlv_raw)

    hw_vlv = np.zeros(n, dtype=np.float32)

    sf_spd_raw = df["SF_SPD"].values.astype(np.float32)
    sf_spd = np.where(sf_spd_raw <= 1.0, sf_spd_raw * 100.0, sf_spd_raw)

    sa_cfm = df["SA_CFM"].values.astype(np.float32)
    sa_sp = df["SA_SP"].values.astype(np.float32)

    # Fan power (Watts -> kW)
    sf_wat = np.maximum(0.0, df["SF_WAT"].values.astype(np.float32))
    rf_wat = np.maximum(0.0, df["RF_WAT"].values.astype(np.float32)) if "RF_WAT" in df.columns else np.zeros(n, dtype=np.float32)
    power = (sf_wat + rf_wat) / 1000.0

    # 2. Derived thermodynamic & aerodynamic features
    delta_t_coil = ma_temp - sa_temp
    delta_t_mixed = oa_temp - ra_temp
    denom_mixed = np.where(np.abs(delta_t_mixed) > 0.1, delta_t_mixed, 0.1)
    mixed_air_ratio = np.clip((ma_temp - ra_temp) / denom_mixed, -2.0, 3.0)
    thermal_load_proxy = sa_cfm * np.abs(ra_temp - sa_temp) * 0.000316
    airflow_per_speed = sa_cfm / (sf_spd + 1e-3)
    sp_per_speed = sa_sp / (sf_spd + 1e-3)
    power_per_airflow = power / np.maximum(sa_cfm, 1.0)
    damper_cooling_fight = np.where((oa_dmpr > 30.0) & (chwc_vlv > 30.0) & (oa_temp > ra_temp), 1.0, 0.0)

    # Clean NaNs/Infs
    def clean_arr(arr: np.ndarray) -> np.ndarray:
        return np.nan_to_num(arr, nan=0.0, posinf=1000.0, neginf=-1000.0)

    feature_dict = {
        "oa_temp": clean_arr(oa_temp),
        "ra_temp": clean_arr(ra_temp),
        "ma_temp": clean_arr(ma_temp),
        "sa_temp": clean_arr(sa_temp),
        "zone_temp": clean_arr(zone_temp),
        "oa_dmpr": clean_arr(oa_dmpr),
        "ra_dmpr": clean_arr(ra_dmpr),
        "chwc_vlv": clean_arr(chwc_vlv),
        "hw_vlv": clean_arr(hw_vlv),
        "sf_spd": clean_arr(sf_spd),
        "sa_cfm": clean_arr(sa_cfm),
        "sa_sp": clean_arr(sa_sp),
        "power": clean_arr(power),
        "delta_t_coil": clean_arr(delta_t_coil),
        "delta_t_mixed": clean_arr(delta_t_mixed),
        "mixed_air_ratio": clean_arr(mixed_air_ratio),
        "thermal_load_proxy": clean_arr(thermal_load_proxy),
        "airflow_per_speed": clean_arr(airflow_per_speed),
        "sp_per_speed": clean_arr(sp_per_speed),
        "power_per_airflow": clean_arr(power_per_airflow),
        "damper_cooling_fight": clean_arr(damper_cooling_fight),
    }

    # Assemble strictly ordered matrices
    X_fault = np.column_stack([feature_dict[feat] for feat in ALL_FAULT_FEATURES]).astype(np.float32)
    X_state = np.column_stack([feature_dict[feat] for feat in STATE_REGRESSOR_INPUT_FEATURES]).astype(np.float32)
    y_state = np.column_stack([feature_dict[tgt] for tgt in STATE_REGRESSOR_TARGETS]).astype(np.float32)

    return X_fault, X_state, y_state


def load_and_prepare_lbnl_dataset(
    dataset_dir: str = DEFAULT_LBNL_DATASET_DIR,
    sample_step: int = 5,  # 5-minute sampling
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> DatasetSplit:
    """
    High-speed vectorized ingestion of real LBNL SDAHU CSV files with chronological 70/15/15 split.
    """
    if not os.path.exists(dataset_dir):
        raise FileNotFoundError(f"LBNL dataset directory not found at: {dataset_dir}")

    csv_files = sorted(glob.glob(os.path.join(dataset_dir, "*.csv")))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in: {dataset_dir}")

    logger.info(f"Discovered {len(csv_files)} LBNL dataset CSV files in {dataset_dir}")

    train_X_fault_list, train_y_fault_list = [], []
    val_X_fault_list, val_y_fault_list = [], []
    test_X_fault_list, test_y_fault_list = [], []

    train_X_state_list, train_y_state_list = [], []
    val_X_state_list, val_y_state_list = [], []
    test_X_state_list, test_y_state_list = [], []

    file_summaries: List[Dict[str, Any]] = []
    date_ranges = {"train": [], "val": [], "test": []}

    for fpath in csv_files:
        fname = os.path.basename(fpath)
        scenario = get_scenario_for_filename(fname)
        label_int = FAULT_LABEL_TO_INT[scenario]

        logger.info(f"Ingesting file '{fname}' (Scenario: {scenario}, Label: {label_int})...")

        # Fast chunked downsampled read
        chunks = []
        for chunk in pd.read_csv(fpath, chunksize=50000):
            chunks.append(chunk.iloc[::sample_step])
        df_sampled = pd.concat(chunks, ignore_index=True)

        df_sampled["Datetime"] = pd.to_datetime(df_sampled["Datetime"])
        df_sampled = df_sampled.sort_values("Datetime").reset_index(drop=True)

        n_rows = len(df_sampled)
        n_train = int(n_rows * train_ratio)
        n_val = int(n_rows * val_ratio)
        n_test = n_rows - n_train - n_val

        df_train = df_sampled.iloc[:n_train]
        df_val = df_sampled.iloc[n_train:n_train + n_val]
        df_test = df_sampled.iloc[n_train + n_val:]

        file_summaries.append({
            "filename": fname,
            "scenario": scenario,
            "total_sampled_rows": n_rows,
            "train_rows": len(df_train),
            "val_rows": len(df_val),
            "test_rows": len(df_test),
            "start_time": str(df_sampled["Datetime"].iloc[0]),
            "end_time": str(df_sampled["Datetime"].iloc[-1]),
        })

        if len(df_train) > 0:
            date_ranges["train"].append((str(df_train["Datetime"].iloc[0]), str(df_train["Datetime"].iloc[-1])))
        if len(df_val) > 0:
            date_ranges["val"].append((str(df_val["Datetime"].iloc[0]), str(df_val["Datetime"].iloc[-1])))
        if len(df_test) > 0:
            date_ranges["test"].append((str(df_test["Datetime"].iloc[0]), str(df_test["Datetime"].iloc[-1])))

        # Vectorized feature computation per split
        train_xf, train_xs, train_ys = extract_features_dataframe_vectorized(df_train)
        val_xf, val_xs, val_ys = extract_features_dataframe_vectorized(df_val)
        test_xf, test_xs, test_ys = extract_features_dataframe_vectorized(df_test)

        train_X_fault_list.append(train_xf)
        train_y_fault_list.append(np.full(len(train_xf), label_int, dtype=np.int32))
        train_X_state_list.append(train_xs)
        train_y_state_list.append(train_ys)

        val_X_fault_list.append(val_xf)
        val_y_fault_list.append(np.full(len(val_xf), label_int, dtype=np.int32))
        val_X_state_list.append(val_xs)
        val_y_state_list.append(val_ys)

        test_X_fault_list.append(test_xf)
        test_y_fault_list.append(np.full(len(test_xf), label_int, dtype=np.int32))
        test_X_state_list.append(test_xs)
        test_y_state_list.append(test_ys)

    # Stack all files
    X_train_fault = np.vstack(train_X_fault_list)
    y_train_fault = np.concatenate(train_y_fault_list)
    X_val_fault = np.vstack(val_X_fault_list)
    y_val_fault = np.concatenate(val_y_fault_list)
    X_test_fault = np.vstack(test_X_fault_list)
    y_test_fault = np.concatenate(test_y_fault_list)

    X_train_state = np.vstack(train_X_state_list)
    y_train_state = np.vstack(train_y_state_list)
    X_val_state = np.vstack(val_X_state_list)
    y_val_state = np.vstack(val_y_state_list)
    X_test_state = np.vstack(test_X_state_list)
    y_test_state = np.vstack(test_y_state_list)

    total_rows = len(X_train_fault) + len(X_val_fault) + len(X_test_fault)

    def get_class_dist(arr: np.ndarray) -> Dict[str, int]:
        unique, counts = np.unique(arr, return_counts=True)
        return {FAULT_INT_TO_LABEL[int(u)]: int(c) for u, c in zip(unique, counts)}

    metadata = {
        "dataset_files": [f["filename"] for f in file_summaries],
        "file_summaries": file_summaries,
        "sample_step_minutes": sample_step,
        "total_rows": total_rows,
        "feature_count": len(ALL_FAULT_FEATURES),
        "feature_names": ALL_FAULT_FEATURES,
        "state_features": STATE_REGRESSOR_INPUT_FEATURES,
        "state_targets": STATE_REGRESSOR_TARGETS,
        "split_strategy": "chronological_70_15_15",
        "train_rows": len(X_train_fault),
        "validation_rows": len(X_val_fault),
        "test_rows": len(X_test_fault),
        "class_distribution": {
            "train": get_class_dist(y_train_fault),
            "val": get_class_dist(y_val_fault),
            "test": get_class_dist(y_test_fault),
        },
        "date_ranges": {
            "train": [date_ranges["train"][0][0], date_ranges["train"][0][1]] if date_ranges["train"] else [],
            "val": [date_ranges["val"][0][0], date_ranges["val"][0][1]] if date_ranges["val"] else [],
            "test": [date_ranges["test"][0][0], date_ranges["test"][0][1]] if date_ranges["test"] else [],
        },
    }

    logger.info("=" * 60)
    logger.info("LBNL DATASET PREPARATION COMPLETE (CHRONOLOGICAL SPLIT)")
    logger.info(f"Total Sampled Rows: {total_rows}")
    logger.info(f"Training Rows:      {len(X_train_fault)} ({len(X_train_fault)/total_rows*100:.1f}%)")
    logger.info(f"Validation Rows:    {len(X_val_fault)} ({len(X_val_fault)/total_rows*100:.1f}%)")
    logger.info(f"Test Rows:          {len(X_test_fault)} ({len(X_test_fault)/total_rows*100:.1f}%)")
    logger.info(f"Feature Count:      {len(ALL_FAULT_FEATURES)}")
    logger.info(f"Class Dist (Train): {metadata['class_distribution']['train']}")
    logger.info(f"Class Dist (Test):  {metadata['class_distribution']['test']}")
    logger.info(f"Train Dates:        {metadata['date_ranges']['train']}")
    logger.info(f"Val Dates:          {metadata['date_ranges']['val']}")
    logger.info(f"Test Dates:         {metadata['date_ranges']['test']}")
    logger.info("=" * 60)

    return DatasetSplit(
        X_train_fault=X_train_fault,
        y_train_fault=y_train_fault,
        X_val_fault=X_val_fault,
        y_val_fault=y_val_fault,
        X_test_fault=X_test_fault,
        y_test_fault=y_test_fault,
        X_train_state=X_train_state,
        y_train_state=y_train_state,
        X_val_state=X_val_state,
        y_val_state=y_val_state,
        X_test_state=X_test_state,
        y_test_state=y_test_state,
        metadata=metadata,
    )


def load_and_prepare_dataset(dataset_dir: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compatibility helper returning (X_fault, y_fault, X_state, y_state)."""
    data = load_and_prepare_lbnl_dataset(dataset_dir or DEFAULTLBNL_DATASET_DIR if 'DEFAULTLBNL_DATASET_DIR' in locals() else DEFAULT_LBNL_DATASET_DIR)
    X_f = np.vstack([data.X_train_fault, data.X_val_fault, data.X_test_fault])
    y_f = np.concatenate([data.y_train_fault, data.y_val_fault, data.y_test_fault])
    X_s = np.vstack([data.X_train_state, data.X_val_state, data.X_test_state])
    y_s = np.vstack([data.y_train_state, data.y_val_state, data.y_test_state])
    return X_f, y_f, X_s, y_s
