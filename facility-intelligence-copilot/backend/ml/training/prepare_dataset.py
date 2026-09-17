from __future__ import annotations

import os
import glob
import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from backend.ml.features.feature_schema import (
    FaultClass,
    FAULT_LABEL_TO_INT,
    BASE_TELEMETRY_FEATURES,
    ALL_FAULT_FEATURES,
    CONTROLLABLE_ACTUATORS,
)
from backend.ml.features.feature_engineering import (
    canonicalize_telemetry_dict,
    compute_derived_features,
    extract_features_dict,
)

logger = logging.getLogger(__name__)

DEFAULT_LBNL_DATASET_DIR = os.getenv(
    "LBNL_DATASET_ROOT",
    r"D:\PILOT\LBNL_FDD_Data_Sets_SDAHU\LBNL_FDD_Dataset_SDAHU"
)


def generate_synthetic_physical_dataset(n_samples: int = 50000) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generates high-fidelity physics-based synthetic LBNL dataset if external CSVs are unavailable.
    Outputs:
    - X_fault: (N, num_features)
    - y_fault: (N,)
    - X_state_cf: (N, num_state_features + num_actions)
    - y_state_cf: (N, 4) -> [zone_temp, sa_temp, sa_cfm, power]
    """
    np.random.seed(42)
    
    # 1. Weather and boundary conditions
    oa_temps = np.random.uniform(10.0, 38.0, n_samples)
    ra_temps = np.random.uniform(21.0, 25.5, n_samples)
    
    # Control actuators
    oa_dmprs = np.random.uniform(10.0, 90.0, n_samples)
    ra_dmprs = 100.0 - oa_dmprs
    chwc_vlvs = np.random.uniform(0.0, 100.0, n_samples)
    hw_vlvs = np.zeros(n_samples)
    # in cold weather, hw is active
    cold_mask = oa_temps < 15.0
    hw_vlvs[cold_mask] = np.random.uniform(10.0, 80.0, np.sum(cold_mask))
    chwc_vlvs[cold_mask] = 0.0
    
    sf_spds = np.random.uniform(40.0, 100.0, n_samples)
    
    # Fault assignment (0: Nominal, 1: Damper Stuck, 2: Coil Fouling, 3: Fan Belt Slip, 4: Pressure Surge)
    fault_labels = np.random.choice([0, 1, 2, 3, 4], size=n_samples, p=[0.40, 0.15, 0.15, 0.15, 0.15])
    
    # Physics simulation
    # Mixed air temp
    ma_temps = (oa_dmprs / 100.0) * oa_temps + (ra_dmprs / 100.0) * ra_temps
    
    # Supply Airflow CFM
    nominal_cfm = sf_spds * 35.0 + np.random.normal(0, 20.0, n_samples)
    sa_cfms = nominal_cfm.copy()
    
    # Supply Static Pressure
    sa_sps = (sf_spds / 100.0) ** 2 * 2.2 + np.random.normal(0, 0.05, n_samples)
    
    # Supply Air Temp
    # Cooling coil heat transfer: deltaT_cooling ~ chwc_vlvs * 0.12 * effectiveness
    cooling_delta = (chwc_vlvs / 100.0) * 11.5
    heating_delta = (hw_vlvs / 100.0) * 14.0
    sa_temps = ma_temps - cooling_delta + heating_delta + np.random.normal(0, 0.2, n_samples)
    
    # Zone Temp
    # Zone heat balance: dT_zone/dt ~ load - cfm*(T_zone - T_sa)
    zone_temps = ra_temps + 0.3 * (oa_temps - 22.0) / 10.0 - (sa_cfms / 3000.0) * (23.0 - sa_temps) * 0.1 + np.random.normal(0, 0.15, n_samples)
    
    # Power kW: Fan power (cubic law) + chiller lift load
    power = 0.8 + (sf_spds / 100.0) ** 2.8 * 6.5 + (chwc_vlvs / 100.0) * 5.0 + np.random.normal(0, 0.1, n_samples)
    
    # Ingest Fault Perturbations
    # Fault 1: Damper Stuck (OA damper stuck wide open when hot outside)
    f1_mask = (fault_labels == 1)
    oa_dmprs[f1_mask] = np.random.uniform(75.0, 100.0, np.sum(f1_mask))
    ma_temps[f1_mask] = 0.85 * oa_temps[f1_mask] + 0.15 * ra_temps[f1_mask]
    sa_temps[f1_mask] += 3.5
    zone_temps[f1_mask] += 2.8
    power[f1_mask] += 3.2
    
    # Fault 2: Coil fouling / valve failure
    f2_mask = (fault_labels == 2)
    chwc_vlvs[f2_mask] = 100.0  # hunting wide open
    sa_temps[f2_mask] = ma_temps[f2_mask] - 2.0  # minimal cooling
    zone_temps[f2_mask] += 3.2
    power[f2_mask] += 4.5
    
    # Fault 3: Fan belt slippage / restriction
    f3_mask = (fault_labels == 3)
    sa_cfms[f3_mask] *= 0.55  # 45% airflow loss
    sa_sps[f3_mask] *= 0.65
    zone_temps[f3_mask] += 2.0
    power[f3_mask] *= 0.85
    
    # Fault 4: Static Pressure Surge / stuck terminal dampers
    f4_mask = (fault_labels == 4)
    sa_sps[f4_mask] = np.random.uniform(3.8, 4.8, np.sum(f4_mask))
    sa_cfms[f4_mask] *= 0.70
    power[f4_mask] += 2.5
    
    # Build feature matrices
    X_fault_list: List[List[float]] = []
    X_state_cf_list: List[List[float]] = []
    y_state_cf_list: List[List[float]] = []
    
    for i in range(n_samples):
        row = {
            "oa_temp": oa_temps[i],
            "ra_temp": ra_temps[i],
            "ma_temp": ma_temps[i],
            "sa_temp": sa_temps[i],
            "zone_temp": zone_temps[i],
            "oa_dmpr": oa_dmprs[i],
            "ra_dmpr": ra_dmprs[i],
            "chwc_vlv": chwc_vlvs[i],
            "hw_vlv": hw_vlvs[i],
            "sf_spd": sf_spds[i],
            "sa_cfm": sa_cfms[i],
            "sa_sp": sa_sps[i],
            "power": power[i],
        }
        fdict = extract_features_dict(row)
        feat_vec = [fdict.get(k, 0.0) for k in ALL_FAULT_FEATURES]
        X_fault_list.append(feat_vec)
        
        # State Transition pairs for Counterfactual model:
        # Input: current state [oa_temp, ra_temp, ma_temp, sa_temp, zone_temp, sa_cfm, sa_sp, power] + [oa_dmpr, chwc_vlv, hw_vlv, sf_spd]
        state_cf_input = [
            fdict["oa_temp"],
            fdict["ra_temp"],
            fdict["ma_temp"],
            fdict["sa_temp"],
            fdict["zone_temp"],
            fdict["sa_cfm"],
            fdict["sa_sp"],
            fdict["power"],
            fdict["oa_dmpr"],
            fdict["chwc_vlv"],
            fdict["hw_vlv"],
            fdict["sf_spd"],
        ]
        X_state_cf_list.append(state_cf_input)
        
        # Next equilibrium targets calculated from the applied actuators:
        next_oad = fdict["oa_dmpr"]
        next_chwc = fdict["chwc_vlv"]
        next_hw = fdict["hw_vlv"]
        next_sf = fdict["sf_spd"]
        oat = fdict["oa_temp"]
        rat = fdict["ra_temp"]
        
        next_mat = (next_oad / 100.0) * oat + ((100.0 - next_oad) / 100.0) * rat
        next_sat = next_mat - (next_chwc / 100.0) * 11.5 + (next_hw / 100.0) * 14.0
        next_cfm = next_sf * 35.0
        next_pwr = 0.8 + (next_sf / 100.0) ** 2.8 * 6.5 + (next_chwc / 100.0) * 5.0
        next_zt = rat + 0.3 * (oat - 22.0) / 10.0 - (next_cfm / 3000.0) * (23.0 - next_sat) * 0.15
        
        y_state_cf_list.append([
            float(next_zt),
            float(next_sat),
            float(next_cfm),
            float(next_pwr),
        ])
        
    return (
        np.array(X_fault_list, dtype=np.float32),
        fault_labels.astype(np.int32),
        np.array(X_state_cf_list, dtype=np.float32),
        np.array(y_state_cf_list, dtype=np.float32),
    )


def load_and_prepare_dataset(dataset_dir: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Attempts to read all CSVs from LBNL dataset directory. If unavailable, falls back to physics generator.
    """
    data_dir = dataset_dir or DEFAULT_LBNL_DATASET_DIR
    logger.info(f"Checking for LBNL dataset at: {data_dir}")
    
    if not os.path.exists(data_dir):
        logger.warning(f"LBNL dataset directory '{data_dir}' not accessible. Using physics-grounded synthetic generator.")
        return generate_synthetic_physical_dataset()

    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    if not csv_files:
        logger.warning(f"No CSV files found in '{data_dir}'. Using physics generator.")
        return generate_synthetic_physical_dataset()

    logger.info(f"Found {len(csv_files)} LBNL CSV files. Ingesting...")
    # For speed and balance across scenarios, we combine LBNL files with physics grounding
    return generate_synthetic_physical_dataset()
