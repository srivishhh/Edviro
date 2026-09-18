from __future__ import annotations

import math
from typing import Any, Dict, List, Union
import numpy as np

from backend.ml.features.feature_schema import (
    BASE_TELEMETRY_FEATURES,
    DERIVED_FEATURES,
    ALL_FAULT_FEATURES,
)

# Common field alias mapping across LBNL dataset CSV headers and BACnet/Modbus telemetry
COLUMN_ALIAS_MAP: Dict[str, str] = {
    # Outdoor Air Temp
    "oa_temp": "oa_temp",
    "oat": "oa_temp",
    "oa_temperature": "oa_temp",
    "outdoorairtemp": "oa_temp",
    "outdoortemp": "oa_temp",
    "oa_t": "oa_temp",
    
    # Return Air Temp
    "ra_temp": "ra_temp",
    "rat": "ra_temp",
    "ra_temperature": "ra_temp",
    "returnairtemp": "ra_temp",
    "returntemp": "ra_temp",
    "ra_t": "ra_temp",

    # Mixed Air Temp
    "ma_temp": "ma_temp",
    "mat": "ma_temp",
    "ma_temperature": "ma_temp",
    "mixedairtemp": "ma_temp",
    "mixedtemp": "ma_temp",
    "ma_t": "ma_temp",

    # Supply Air Temp
    "sa_temp": "sa_temp",
    "sat": "sa_temp",
    "sa_temperature": "sa_temp",
    "supplyairtemp": "sa_temp",
    "supplytemp": "sa_temp",
    "sa_t": "sa_temp",

    # Zone Temp
    "zone_temp": "zone_temp",
    "zt": "zone_temp",
    "zone_temperature": "zone_temp",
    "zonetemp": "zone_temp",
    "space_temp": "zone_temp",
    "temp": "zone_temp",
    "temperature": "zone_temp",

    # Outdoor Air Damper
    "oa_dmpr": "oa_dmpr",
    "oad": "oa_dmpr",
    "oa_damper": "oa_dmpr",
    "damper": "oa_dmpr",
    "damper_position": "oa_dmpr",
    "damper_pos": "oa_dmpr",

    # Return Air Damper
    "ra_dmpr": "ra_dmpr",
    "rad": "ra_dmpr",
    "ra_damper": "ra_dmpr",

    # Cooling Valve
    "chwc_vlv": "chwc_vlv",
    "chwc": "chwc_vlv",
    "cooling_valve": "chwc_vlv",
    "cooling_coil_valve": "chwc_vlv",
    "chw_valve": "chwc_vlv",
    "clg_vlv": "chwc_vlv",

    # Heating Valve
    "hw_vlv": "hw_vlv",
    "hwc": "hw_vlv",
    "heating_valve": "hw_vlv",
    "heating_coil_valve": "hw_vlv",
    "htg_vlv": "hw_vlv",

    # Supply Fan Speed
    "sf_spd": "sf_spd",
    "fan_speed": "sf_spd",
    "sf_speed": "sf_spd",
    "supply_fan_speed": "sf_spd",
    "vfd_speed": "sf_spd",

    # Airflow
    "sa_cfm": "sa_cfm",
    "airflow": "sa_cfm",
    "supply_airflow": "sa_cfm",
    "sa_flow": "sa_cfm",
    "cfm": "sa_cfm",

    # Static Pressure
    "sa_sp": "sa_sp",
    "pressure": "sa_sp",
    "static_pressure": "sa_sp",
    "duct_pressure": "sa_sp",
    "sp": "sa_sp",

    # Power
    "power": "power",
    "pwr": "power",
    "electric_power": "power",
    "kw": "power",
    "energy": "power",
}

# Domain default values when a sensor is momentarily unmapped
DEFAULT_NOMINAL_TELEMETRY: Dict[str, float] = {
    "oa_temp": 65.0,
    "ra_temp": 72.0,
    "ma_temp": 68.0,
    "sa_temp": 55.0,
    "zone_temp": 72.0,
    "oa_dmpr": 20.0,
    "ra_dmpr": 80.0,
    "chwc_vlv": 35.0,
    "hw_vlv": 0.0,
    "sf_spd": 70.0,
    "sa_cfm": 2500.0,
    "sa_sp": 1.5,
    "power": 8.5,
}


def validate_telemetry_dict(raw: Dict[str, Any]) -> None:
    """
    Validates that telemetry dictionary is non-empty and contains non-infinite, non-corrupted values.
    Raises ValueError on fatal schema violations.
    """
    if not isinstance(raw, dict):
        raise ValueError(f"Telemetry payload must be a dict, got {type(raw).__name__}")
    if not raw:
        raise ValueError("Telemetry payload cannot be empty")

    for k, v in raw.items():
        if v is not None:
            try:
                fv = float(v)
                if math.isinf(fv):
                    raise ValueError(f"Feature '{k}' contains Inf value: {v}")
                if math.isnan(fv):
                    raise ValueError(f"Feature '{k}' contains NaN value: {v}")
            except (TypeError, ValueError) as ex:
                if "Inf" in str(ex) or "NaN" in str(ex):
                    raise ex
                # String timestamps or metadata are allowed


def canonicalize_telemetry_dict(raw: Dict[str, Any]) -> Dict[str, float]:
    """
    Normalizes arbitrary casing, aliases, zone averages, fan powers, and string types into standard float dictionary.
    """
    canonical: Dict[str, float] = {}
    
    # Check for multi-zone average if zone_temp is not directly provided
    zone_temps = []
    for z_idx in range(1, 6):
        for key in [f"ZONE_TEMP_{z_idx}", f"zone_temp_{z_idx}", f"zt_{z_idx}"]:
            if key in raw and raw[key] is not None:
                try:
                    zone_temps.append(float(raw[key]))
                    break
                except (ValueError, TypeError):
                    pass
    if zone_temps and "zone_temp" not in raw and "ZONE_TEMP" not in raw:
        canonical["zone_temp"] = sum(zone_temps) / len(zone_temps)

    # Check for fan power aggregation (SF_WAT + RF_WAT) -> kW
    sf_wat = raw.get("SF_WAT", raw.get("sf_wat"))
    rf_wat = raw.get("RF_WAT", raw.get("rf_wat"))
    if (sf_wat is not None or rf_wat is not None) and "power" not in raw and "POWER" not in raw:
        try:
            sf_val = max(0.0, float(sf_wat)) if sf_wat is not None else 0.0
            rf_val = max(0.0, float(rf_wat)) if rf_wat is not None else 0.0
            canonical["power"] = (sf_val + rf_val) / 1000.0  # W to kW
        except (ValueError, TypeError):
            pass

    # First pass: map known aliases
    for k, v in raw.items():
        clean_k = str(k).strip().lower().replace(" ", "_").replace("-", "_")
        canonical_key = COLUMN_ALIAS_MAP.get(clean_k, clean_k)
        if canonical_key in BASE_TELEMETRY_FEATURES:
            try:
                val = float(v)
                # Handle fraction vs percentage for actuators (0.0 - 1.0 -> 0.0 - 100.0%)
                if canonical_key in ["oa_dmpr", "ra_dmpr", "chwc_vlv", "hw_vlv", "sf_spd"]:
                    if 0.0 < val <= 1.0 and "pct" not in clean_k:
                        val = val * 100.0
                canonical[canonical_key] = val
            except (ValueError, TypeError):
                canonical[canonical_key] = DEFAULT_NOMINAL_TELEMETRY.get(canonical_key, 0.0)

    # Second pass: fill missing baseline channels with domain defaults
    for feat in BASE_TELEMETRY_FEATURES:
        if feat not in canonical:
            canonical[feat] = DEFAULT_NOMINAL_TELEMETRY.get(feat, 0.0)

    return canonical


def compute_derived_features(base: Dict[str, float]) -> Dict[str, float]:
    """
    Computes physical thermodynamic and aerodynamic relations from base channels.
    """
    ma = base.get("ma_temp", 68.0)
    sa = base.get("sa_temp", 55.0)
    oa = base.get("oa_temp", 65.0)
    ra = base.get("ra_temp", 72.0)
    cfm = base.get("sa_cfm", 2500.0)
    spd = max(base.get("sf_spd", 70.0), 1.0)
    sp = base.get("sa_sp", 1.5)
    pwr = base.get("power", 8.5)
    oad = base.get("oa_dmpr", 20.0)
    chwc = base.get("chwc_vlv", 35.0)

    delta_t_coil = ma - sa
    delta_t_mixed = oa - ra
    denom_mixed = delta_t_mixed if abs(delta_t_mixed) > 0.1 else 0.1
    mixed_air_ratio = float(np.clip((ma - ra) / denom_mixed, -2.0, 3.0))
    thermal_load_proxy = cfm * abs(ra - sa) * 0.000316
    airflow_per_speed = cfm / spd
    sp_per_speed = sp / spd
    power_per_airflow = pwr / max(cfm, 1.0)
    damper_cooling_fight = 1.0 if (oad > 30.0 and chwc > 30.0 and oa > ra) else 0.0

    return {
        "delta_t_coil": delta_t_coil,
        "delta_t_mixed": delta_t_mixed,
        "mixed_air_ratio": mixed_air_ratio,
        "thermal_load_proxy": thermal_load_proxy,
        "airflow_per_speed": airflow_per_speed,
        "sp_per_speed": sp_per_speed,
        "power_per_airflow": power_per_airflow,
        "damper_cooling_fight": damper_cooling_fight,
    }


def extract_features_dict(raw: Dict[str, Any]) -> Dict[str, float]:
    """
    Returns full dictionary of base + derived features.
    """
    validate_telemetry_dict(raw)
    canonical = canonicalize_telemetry_dict(raw)
    derived = compute_derived_features(canonical)
    return {**canonical, **derived}


def extract_feature_vector(raw: Dict[str, Any], feature_names: List[str] = ALL_FAULT_FEATURES) -> np.ndarray:
    """
    Produces a strictly ordered 1D numpy array of features ready for model inference.
    """
    full_dict = extract_features_dict(raw)
    vec = [full_dict.get(fname, 0.0) for fname in feature_names]
    return np.array(vec, dtype=np.float32)
