from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class FaultClass(str, Enum):
    NOMINAL = "nominal"
    DAMPER_STUCK = "damper_stuck"
    COIL_FOULING_OR_LEAKAGE = "coil_fouling_or_leakage"
    FAN_BELT_SLIP = "fan_belt_slip"
    STATIC_PRESSURE_SURGE = "static_pressure_surge"


FAULT_LABEL_TO_INT: Dict[str, int] = {
    FaultClass.NOMINAL.value: 0,
    FaultClass.DAMPER_STUCK.value: 1,
    FaultClass.COIL_FOULING_OR_LEAKAGE.value: 2,
    FaultClass.FAN_BELT_SLIP.value: 3,
    FaultClass.STATIC_PRESSURE_SURGE.value: 4,
}

FAULT_INT_TO_LABEL: Dict[int, str] = {v: k for k, v in FAULT_LABEL_TO_INT.items()}


# Standard Base Telemetry Channel Names in LBNL Dataset and GSENSE Twin
BASE_TELEMETRY_FEATURES: List[str] = [
    "oa_temp",    # Outdoor Air Temp (°C / °F)
    "ra_temp",    # Return Air Temp (°C / °F)
    "ma_temp",    # Mixed Air Temp (°C / °F)
    "sa_temp",    # Supply Air Temp (°C / °F)
    "zone_temp",  # Zone Average Temp (°C / °F)
    "oa_dmpr",    # Outdoor Air Damper Command (%)
    "ra_dmpr",    # Return Air Damper Command (%)
    "chwc_vlv",   # Chilled Water Cooling Coil Valve (%)
    "hw_vlv",     # Hot Water Heating Coil Valve (%)
    "sf_spd",     # Supply Fan Speed (%)
    "sa_cfm",     # Supply Air Volumetric Flow (CFM)
    "sa_sp",      # Supply Air Static Pressure (in. w.g.)
    "power",      # Power consumption (kW)
]

# Engineered thermodynamic and aerodynamic features
DERIVED_FEATURES: List[str] = [
    "delta_t_coil",         # MA_TEMP - SA_TEMP
    "delta_t_mixed",        # OA_TEMP - RA_TEMP
    "mixed_air_ratio",      # (MA_TEMP - RA_TEMP) / (OA_TEMP - RA_TEMP + eps)
    "thermal_load_proxy",   # SA_CFM * abs(RA_TEMP - SA_TEMP) * 0.000316
    "airflow_per_speed",    # SA_CFM / (SF_SPD + 1e-3)
    "sp_per_speed",         # SA_SP / (SF_SPD + 1e-3)
    "power_per_airflow",    # POWER / (SA_CFM + 1e-3)
    "damper_cooling_fight", # 1.0 if (oa_dmpr > 40 and chwc_vlv > 50 and oa_temp > ra_temp) else 0.0
]

ALL_FAULT_FEATURES: List[str] = BASE_TELEMETRY_FEATURES + DERIVED_FEATURES

# Controllable Actuators (Candidate Interventions)
CONTROLLABLE_ACTUATORS: List[str] = [
    "oa_dmpr",
    "chwc_vlv",
    "hw_vlv",
    "sf_spd",
]

# Physical bounds for simulation validation
ACTUATOR_BOUNDS: Dict[str, Tuple[float, float]] = {
    "oa_dmpr": (0.0, 100.0),
    "ra_dmpr": (0.0, 100.0),
    "chwc_vlv": (0.0, 100.0),
    "hw_vlv": (0.0, 100.0),
    "sf_spd": (20.0, 100.0),
}

# Comfort & Safety Operating Envelopes
OPERATING_CONSTRAINTS: Dict[str, Tuple[float, float]] = {
    "zone_temp": (19.0, 26.0),    # Target comfort band (°C)
    "sa_temp": (12.0, 30.0),      # Physical supply air limits (°C)
    "sa_sp": (0.5, 4.5),          # Duct static pressure limits (in. w.g.)
    "sa_cfm": (100.0, 10000.0),   # Airflow limits (CFM)
    "power": (0.5, 50.0),         # Maximum AHU branch electrical power (kW)
}
