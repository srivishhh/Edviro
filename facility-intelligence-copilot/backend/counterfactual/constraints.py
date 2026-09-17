from __future__ import annotations

from typing import Dict, List, Tuple
from backend.counterfactual.schemas import ConstraintViolation, ValidationStatus
from backend.ml.features.feature_schema import OPERATING_CONSTRAINTS, ACTUATOR_BOUNDS


class ConstraintChecker:
    """
    Deterministic validator enforcing physics, safety envelopes, and ASHRAE comfort limits.
    """

    @classmethod
    def evaluate_constraints(
        cls,
        current_state: Dict[str, float],
        interventions: Dict[str, float],
        predicted_state: Dict[str, float],
    ) -> Tuple[ValidationStatus, List[ConstraintViolation], float]:
        """
        Runs all deterministic checks against candidate intervention and resulting state.
        Returns:
            - status: VALIDATED, REJECTED, or NEEDS_REVIEW
            - violations: List of detailed violations
            - score: Confidence/fitness score (0.0 - 1.0)
        """
        violations: List[ConstraintViolation] = []
        
        # 1. Physical Actuator Limit Checks
        for act, val in interventions.items():
            bounds = ACTUATOR_BOUNDS.get(act, (0.0, 100.0))
            if val < bounds[0] or val > bounds[1]:
                violations.append(
                    ConstraintViolation(
                        constraint_name="PHYSICAL_ACTUATOR_LIMIT",
                        description=f"Proposed actuator '{act}' value {val:.1f}% exceeds physical limits [{bounds[0]}%, {bounds[1]}%].",
                        metric=act,
                        actual_value=val,
                        allowed_limit=f"{bounds[0]}% - {bounds[1]}%",
                        severity="CRITICAL",
                    )
                )

        # 2. Zone Comfort Band Check (ASHRAE 55)
        pred_zone_temp = predicted_state.get("zone_temp", 22.8)
        cur_zone_temp = current_state.get("zone_temp", pred_zone_temp)
        is_f = pred_zone_temp > 45.0
        min_temp, max_temp = (66.0, 80.6) if is_f else (19.0, 27.0)
        unit = "°F" if is_f else "°C"

        if pred_zone_temp > max_temp:
            is_improving = pred_zone_temp < cur_zone_temp
            violations.append(
                ConstraintViolation(
                    constraint_name="ASHRAE_THERMAL_COMFORT_CEILING",
                    description=f"Predicted zone temperature {pred_zone_temp:.2f}{unit} violates upper comfort limit {max_temp:.1f}{unit}.",
                    metric="zone_temp",
                    actual_value=pred_zone_temp,
                    allowed_limit=f"<= {max_temp}{unit}",
                    severity="HIGH" if is_improving else "CRITICAL",
                )
            )
        elif pred_zone_temp < min_temp:
            is_improving = pred_zone_temp > cur_zone_temp
            violations.append(
                ConstraintViolation(
                    constraint_name="ASHRAE_THERMAL_COMFORT_FLOOR",
                    description=f"Predicted zone temperature {pred_zone_temp:.2f}{unit} violates lower comfort limit {min_temp:.1f}{unit}.",
                    metric="zone_temp",
                    actual_value=pred_zone_temp,
                    allowed_limit=f">= {min_temp}{unit}",
                    severity="HIGH" if is_improving else "CRITICAL",
                )
            )

        # 3. Duct Static Pressure Safety Ceiling
        pred_sp = predicted_state.get("sa_sp", 1.5)
        sp_min, sp_max = OPERATING_CONSTRAINTS["sa_sp"]
        if pred_sp > sp_max:
            violations.append(
                ConstraintViolation(
                    constraint_name="DUCT_OVERPRESSURE_RISK",
                    description=f"Static pressure {pred_sp:.2f} in.w.g. exceeds duct acoustic/rupture limit {sp_max:.1f} in.w.g.",
                    metric="sa_sp",
                    actual_value=pred_sp,
                    allowed_limit=f"<= {sp_max} in.w.g.",
                    severity="CRITICAL",
                )
            )

        # 4. Anti-Freeze Coil Protection Check
        oa_t = predicted_state.get("oa_temp", 24.0)
        oa_dmpr = interventions.get("oa_dmpr", predicted_state.get("oa_dmpr", 25.0))
        oa_is_f = oa_t > 45.0
        freeze_thresh = 39.2 if oa_is_f else 4.0
        oa_unit = "°F" if oa_is_f else "°C"

        if oa_t < freeze_thresh and oa_dmpr > 40.0:
            violations.append(
                ConstraintViolation(
                    constraint_name="COIL_FREEZE_PROTECTION",
                    description=f"Outdoor air damper {oa_dmpr:.1f}% at ambient {oa_t:.1f}{oa_unit} risks freezing cooling coil water tubes.",
                    metric="oa_dmpr",
                    actual_value=oa_dmpr,
                    allowed_limit=f"<= 40% when OAT < {freeze_thresh:.1f}{oa_unit}",
                    severity="CRITICAL",
                )
            )

        # 5. Determine status and score
        critical_violations = [v for v in violations if v.severity == "CRITICAL"]
        high_violations = [v for v in violations if v.severity == "HIGH"]

        if critical_violations:
            status = ValidationStatus.REJECTED
            score = max(0.0, 0.30 - len(critical_violations) * 0.15)
        elif high_violations:
            status = ValidationStatus.NEEDS_REVIEW
            score = max(0.40, 0.70 - len(high_violations) * 0.15)
        else:
            status = ValidationStatus.VALIDATED
            # Score bonus for energy efficiency and comfort stabilization
            cur_power = current_state.get("power", 8.5)
            pred_power = predicted_state.get("power", cur_power)
            energy_reduction_ratio = max(0.0, (cur_power - pred_power) / max(cur_power, 1.0))
            score = min(0.99, 0.85 + energy_reduction_ratio * 0.14)

        return status, violations, round(score, 3)
