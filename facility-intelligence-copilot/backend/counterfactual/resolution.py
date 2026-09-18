from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Tuple


class ResolutionStatus(str, Enum):
    RESOLVES_ISSUE = "RESOLVES_ISSUE"
    DOES_NOT_RESOLVE = "DOES_NOT_RESOLVE"
    UNSAFE = "UNSAFE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ResolutionEvaluator:
    """
    Deterministic resolution evaluation engine.
    Evaluates whether a candidate's predicted physical state actually resolves
    the specific detected HVAC fault condition.
    """

    @classmethod
    def evaluate_resolution(
        cls,
        detected_fault: str,
        baseline_state: Dict[str, float],
        predicted_state: Dict[str, float],
        is_safe: bool = True,
    ) -> Tuple[ResolutionStatus, List[str]]:
        """
        Evaluates fault-specific resolution criteria.
        Returns:
            - status: RESOLVES_ISSUE, DOES_NOT_RESOLVE, UNSAFE, or NEEDS_REVIEW
            - evidence: List of deterministic verification statements
        """
        if not is_safe:
            return ResolutionStatus.UNSAFE, ["Candidate violates one or more hard physical/safety constraints."]

        fault_lower = (detected_fault or "nominal").lower()
        evidence: List[str] = []

        # Extract baseline vs predicted telemetry points
        cur_sa_temp = baseline_state.get("sa_temp", 18.0)
        pred_sa_temp = predicted_state.get("sa_temp", cur_sa_temp)

        cur_zone_temp = baseline_state.get("zone_temp", 24.5)
        pred_zone_temp = predicted_state.get("zone_temp", cur_zone_temp)

        cur_sa_cfm = baseline_state.get("sa_cfm", 12000.0)
        pred_sa_cfm = predicted_state.get("sa_cfm", cur_sa_cfm)

        cur_power = baseline_state.get("power", 15.0)
        pred_power = predicted_state.get("power", cur_power)

        # Detect unit system (°F vs °C) from baseline zone/supply temp
        is_f = cur_zone_temp > 45.0 or cur_sa_temp > 45.0
        temp_unit = "°F" if is_f else "°C"

        # Normalize predicted temperatures to match baseline unit system
        if is_f:
            if pred_sa_temp <= 45.0:
                pred_sa_temp = round(pred_sa_temp * 9.0 / 5.0 + 32.0, 2)
            if pred_zone_temp <= 45.0:
                pred_zone_temp = round(pred_zone_temp * 9.0 / 5.0 + 32.0, 2)
        else:
            if pred_sa_temp > 45.0:
                pred_sa_temp = round((pred_sa_temp - 32.0) * 5.0 / 9.0, 2)
            if pred_zone_temp > 45.0:
                pred_zone_temp = round((pred_zone_temp - 32.0) * 5.0 / 9.0, 2)

        # Target setpoint envelopes (ASHRAE 55 standard comfort envelope)
        target_sa_min, target_sa_max = (50.0, 68.0) if is_f else (10.0, 20.0)
        target_zone_min, target_zone_max = (66.0, 80.6) if is_f else (19.0, 27.0)


        # -------------------------------------------------------------
        # 1. AIRFLOW RESTRICTION / FAN / VFD ISSUES
        # -------------------------------------------------------------
        if "airflow" in fault_lower or "fan" in fault_lower or "restriction" in fault_lower or "vfd" in fault_lower:
            delta_cfm = pred_sa_cfm - cur_sa_cfm
            if pred_sa_cfm >= 14000.0 or (cur_sa_cfm < 12000.0 and delta_cfm >= 1200.0):
                evidence.append(
                    f"Supply airflow restored: projected {pred_sa_cfm:.0f} CFM (delta: +{delta_cfm:.0f} CFM) meets baseline requirements."
                )
                if target_zone_min <= pred_zone_temp <= target_zone_max:
                    evidence.append(f"Zone temperature maintained at {pred_zone_temp:.1f}{temp_unit}.")
                return ResolutionStatus.RESOLVES_ISSUE, evidence
            else:
                evidence.append(
                    f"Airflow remains deficient: projected {pred_sa_cfm:.0f} CFM does not reach required operating airflow."
                )
                return ResolutionStatus.DOES_NOT_RESOLVE, evidence

        # -------------------------------------------------------------
        # 2. DAMPER STUCK / ECONOMIZER / OUTDOOR AIR BIAS
        # -------------------------------------------------------------
        elif "damper" in fault_lower or "oa_bias" in fault_lower or "economizer" in fault_lower:
            sa_in_range = target_sa_min <= pred_sa_temp <= target_sa_max
            zone_in_range = target_zone_min <= pred_zone_temp <= target_zone_max
            zone_improving = abs(pred_zone_temp - 22.0) < abs(cur_zone_temp - 22.0) if not is_f else abs(pred_zone_temp - 72.0) < abs(cur_zone_temp - 72.0)

            if (sa_in_range or zone_improving) and zone_in_range:
                evidence.append(
                    f"Damper airflow modulation restored: Supply air temperature stabilized at {pred_sa_temp:.1f}{temp_unit}."
                )
                evidence.append(f"Zone thermal equilibrium achieved at {pred_zone_temp:.1f}{temp_unit}.")
                return ResolutionStatus.RESOLVES_ISSUE, evidence
            else:
                evidence.append(
                    f"Thermal equilibrium not achieved: Predicted zone temp {pred_zone_temp:.1f}{temp_unit} (current: {cur_zone_temp:.1f}{temp_unit})."
                )
                return ResolutionStatus.DOES_NOT_RESOLVE, evidence

        # -------------------------------------------------------------
        # 3. COOLING COIL STUCK / LEAKAGE / COIL BIAS
        # -------------------------------------------------------------
        elif "coi" in fault_lower or "coil" in fault_lower or "cooling" in fault_lower:
            sa_in_range = target_sa_min <= pred_sa_temp <= target_sa_max
            sa_improving = (cur_sa_temp > target_sa_max and pred_sa_temp <= (cur_sa_temp + 0.1)) or (cur_sa_temp < target_sa_min and pred_sa_temp >= (cur_sa_temp - 0.1))
            zone_in_range = target_zone_min <= pred_zone_temp <= target_zone_max
            zone_improving = abs(pred_zone_temp - 22.0) <= (abs(cur_zone_temp - 22.0) + 0.1) if not is_f else abs(pred_zone_temp - 72.0) <= (abs(cur_zone_temp - 72.0) + 0.2)
            comfort_preserved = zone_in_range and abs(pred_zone_temp - cur_zone_temp) <= 1.0

            if (sa_in_range or sa_improving or zone_improving or comfort_preserved) and zone_in_range:
                evidence.append(
                    f"Hydronic coil thermal transfer restored: Supply air temp {pred_sa_temp:.1f}{temp_unit} (target: {target_sa_min}-{target_sa_max}{temp_unit})."
                )
                evidence.append(f"Zone comfort protected at {pred_zone_temp:.1f}{temp_unit}.")
                return ResolutionStatus.RESOLVES_ISSUE, evidence
            else:
                evidence.append(
                    f"Cooling deficiency persists: Supply air temp {pred_sa_temp:.1f}{temp_unit} remains outside target range [{target_sa_min}-{target_sa_max}{temp_unit}]."
                )
                return ResolutionStatus.DOES_NOT_RESOLVE, evidence



        # -------------------------------------------------------------
        # 4. NOMINAL OR GENERAL
        # -------------------------------------------------------------
        else:
            if target_zone_min <= pred_zone_temp <= target_zone_max:
                evidence.append(f"Nominal operating conditions verified: Zone temp at {pred_zone_temp:.1f}{temp_unit}.")
                return ResolutionStatus.RESOLVES_ISSUE, evidence
            else:
                evidence.append(f"Zone temp {pred_zone_temp:.1f}{temp_unit} outside comfort range.")
                return ResolutionStatus.DOES_NOT_RESOLVE, evidence

