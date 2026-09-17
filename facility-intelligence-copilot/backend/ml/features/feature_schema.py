from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Tuple


class FaultClass(str, Enum):
    NOMINAL = "nominal"
    DAMPER_STUCK = "damper_stuck"
    COI_STUCK = "coi_stuck"
    COI_LEAKAGE = "coi_leakage"
    COI_BIAS = "coi_bias"
    OA_BIAS = "oa_bias"
    # Legacy / alias compatibility
    COIL_FOULING_OR_LEAKAGE = "coil_fouling_or_leakage"
    FAN_BELT_SLIP = "fan_belt_slip"
    STATIC_PRESSURE_SURGE = "static_pressure_surge"


# Canonical integer mappings for training and evaluation
FAULT_LABEL_TO_INT: Dict[str, int] = {
    FaultClass.NOMINAL.value: 0,
    FaultClass.DAMPER_STUCK.value: 1,
    FaultClass.COI_STUCK.value: 2,
    FaultClass.COI_LEAKAGE.value: 3,
    FaultClass.COI_BIAS.value: 4,
    FaultClass.OA_BIAS.value: 5,
}

FAULT_INT_TO_LABEL: Dict[int, str] = {v: k for k, v in FAULT_LABEL_TO_INT.items()}

# Mapping from scenario filenames / keywords to canonical labels
FILENAME_SCENARIO_MAP: Dict[str, str] = {
    "AHU_annual": FaultClass.NOMINAL.value,
    "damper_stuck": FaultClass.DAMPER_STUCK.value,
    "coi_stuck": FaultClass.COI_STUCK.value,
    "coi_leakage": FaultClass.COI_LEAKAGE.value,
    "coi_bias": FaultClass.COI_BIAS.value,
    "oa_bias": FaultClass.OA_BIAS.value,
}

# Base Telemetry Channels (13 canonical physical channels)
BASE_TELEMETRY_FEATURES: List[str] = [
    "oa_temp",    # Outdoor Air Temp (°F / °C)
    "ra_temp",    # Return Air Temp (°F / °C)
    "ma_temp",    # Mixed Air Temp (°F / °C)
    "sa_temp",    # Supply Air Temp (°F / °C)
    "zone_temp",  # Zone Average Temp (°F / °C)
    "oa_dmpr",    # Outdoor Air Damper Command (%)
    "ra_dmpr",    # Return Air Damper Command (%)
    "chwc_vlv",   # Chilled Water Cooling Coil Valve (%)
    "hw_vlv",     # Hot Water Heating Coil Valve (%)
    "sf_spd",     # Supply Fan Speed (%)
    "sa_cfm",     # Supply Air Volumetric Flow (CFM)
    "sa_sp",      # Supply Air Static Pressure (in. w.g. / Pa)
    "power",      # Electric power (kW)
]

# Engineered thermodynamic and aerodynamic features (8 derived physical features)
DERIVED_FEATURES: List[str] = [
    "delta_t_coil",         # MA_TEMP - SA_TEMP: Sensible cooling coil delta-T
    "delta_t_mixed",        # OA_TEMP - RA_TEMP: Outdoor vs Return thermal gradient
    "mixed_air_ratio",      # (MA_TEMP - RA_TEMP) / (OA_TEMP - RA_TEMP + eps): Economizer ratio
    "thermal_load_proxy",   # SA_CFM * abs(RA_TEMP - SA_TEMP) * 1.08: Sensible load proxy
    "airflow_per_speed",    # SA_CFM / (SF_SPD + 1e-3): Fan aerodynamic yield
    "sp_per_speed",         # SA_SP / (SF_SPD + 1e-3): Duct aerodynamic resistance
    "power_per_airflow",    # POWER / (SA_CFM + 1e-3): Specific energy intensity
    "damper_cooling_fight", # 1.0 if (oa_dmpr > 30 and chwc_vlv > 30 and oa_temp > ra_temp) else 0.0
]

# Ordered full feature list for model input (deterministic order guaranteed)
ALL_FAULT_FEATURES: List[str] = BASE_TELEMETRY_FEATURES + DERIVED_FEATURES

# Controllable Actuators (Candidate Interventions)
CONTROLLABLE_ACTUATORS: List[str] = [
    "oa_dmpr",
    "chwc_vlv",
    "hw_vlv",
    "sf_spd",
]

# State Regressor Inputs: current state features + proposed actuator settings
STATE_REGRESSOR_INPUT_FEATURES: List[str] = [
    "oa_temp",
    "ra_temp",
    "ma_temp",
    "sa_temp",
    "zone_temp",
    "sa_cfm",
    "sa_sp",
    "power",
    "oa_dmpr",
    "chwc_vlv",
    "hw_vlv",
    "sf_spd",
]

# State Regressor Target Channels
STATE_REGRESSOR_TARGETS: List[str] = [
    "zone_temp",
    "sa_temp",
    "sa_cfm",
    "power",
]

# Physical bounds for validation
ACTUATOR_BOUNDS: Dict[str, Tuple[float, float]] = {
    "oa_dmpr": (0.0, 100.0),
    "ra_dmpr": (0.0, 100.0),
    "chwc_vlv": (0.0, 100.0),
    "hw_vlv": (0.0, 100.0),
    "sf_spd": (20.0, 100.0),
}

# Comfort & Safety Operating Envelopes
OPERATING_CONSTRAINTS: Dict[str, Tuple[float, float]] = {
    "zone_temp": (19.0, 27.0),    # Target comfort band (°C: 19-27) or (°F: 66-80.6)
    "sa_temp": (12.0, 30.0),      # Physical supply air limits (°C)
    "sa_sp": (0.5, 4.5),          # Duct static pressure limits (in. w.g.)
    "sa_cfm": (100.0, 10000.0),   # Airflow limits (CFM)
    "power": (0.5, 50.0),         # Maximum AHU branch electrical power (kW)
}
