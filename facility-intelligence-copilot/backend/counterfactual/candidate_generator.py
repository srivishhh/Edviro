from __future__ import annotations

from typing import Dict, List, Optional, Any, Tuple
from backend.counterfactual.schemas import CandidatePlan, CandidateAction
from backend.ml.features.feature_schema import FaultClass, ACTUATOR_BOUNDS

import logging

logger = logging.getLogger(__name__)


class CandidateGenerator:
    """
    Synthesizes diverse, independent intervention candidates for counterfactual validation.

    CRITICAL DESIGN RULE:
    Each CandidatePlan must be simulated as a completely INDEPENDENT Digital Twin branch.
    Candidates are NEVER merged before simulation.
    The baseline telemetry is always copied fresh for each candidate.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def from_sns_candidate_list(
        cls,
        sns_candidate_actions: List[Dict[str, Any]],
        current_telemetry: Dict[str, float],
    ) -> List[CandidatePlan]:
        """
        Convert a list of SNS candidate_actions directly into independent CandidatePlan objects.

        Each SNS candidate action → one independent CandidatePlan.
        This preserves the independence of each Digital Twin simulation branch.
        No merging occurs here.
        """
        plans: List[CandidatePlan] = []
        for i, action in enumerate(sns_candidate_actions):
            action_id = action.get("action_id", f"SNS-CAND-{i+1:02d}")
            target = action.get("target", "")
            try:
                proposed_value = float(action.get("proposed_value", 0))
            except (TypeError, ValueError):
                logger.warning(f"[CandidateGen] Skipping {action_id}: invalid proposed_value")
                continue

            if not target:
                logger.warning(f"[CandidateGen] Skipping {action_id}: missing target actuator")
                continue

            # Validate bounds
            bounds = ACTUATOR_BOUNDS.get(target, (0.0, 100.0))
            if proposed_value < bounds[0] or proposed_value > bounds[1]:
                logger.warning(
                    f"[CandidateGen] Skipping {action_id}: {target}={proposed_value} "
                    f"outside bounds [{bounds[0]}, {bounds[1]}]"
                )
                continue

            current_val = float(current_telemetry.get(target, action.get("current_value", proposed_value)))

            # Skip no-ops
            if abs(proposed_value - current_val) < 0.5:
                logger.debug(f"[CandidateGen] Skipping {action_id}: no-op ({target}: {current_val} → {proposed_value})")
                continue

            candidate_id = f"cand_sns_{action_id.lower().replace('-', '_')}"
            reason = action.get("reason", f"SNS 3.0 GSense intervention on {target}.")
            objective = action.get("expected_objective", f"Modulate {target} to {proposed_value}%")

            cand_action = CandidateAction(
                action_id=action_id,
                target=target,
                parameter="value",
                current_value=round(current_val, 1),
                proposed_value=round(proposed_value, 1),
                reason=reason,
                expected_objective=objective,
            )

            plans.append(
                CandidatePlan(
                    candidate_id=candidate_id,
                    title=f"SNS: {action_id} — {target.upper()} → {proposed_value:.0f}%",
                    description=reason,
                    proposed_by="SNS_COGNITIVE_AGENT",
                    interventions={target: proposed_value},
                    actions=[cand_action],
                    expected_rationale=objective,
                )
            )

        logger.info(f"[CandidateGen] from_sns_candidate_list → {len(plans)} independent SNS branches")
        return plans

    @classmethod
    def generate_candidates(
        cls,
        fault_class: str,
        current_telemetry: Dict[str, float],
        sns_proposed_plan: Optional[Dict[str, Any]] = None,
    ) -> List[CandidatePlan]:
        """
        Generate domain-specific candidates for the diagnosed fault.

        If sns_proposed_plan is provided (legacy path), it is added as ONE candidate.
        The primary path is now from_sns_candidate_list() for independent branch simulation.
        """
        candidates: List[CandidatePlan] = []

        cur_oad  = current_telemetry.get("oa_dmpr",  25.0)
        cur_chwc = current_telemetry.get("chwc_vlv", 35.0)
        cur_sf   = current_telemetry.get("sf_spd",   70.0)

        # Legacy: single SNS proposed plan
        if sns_proposed_plan and "interventions" in sns_proposed_plan:
            sns_interventions = {k: float(v) for k, v in sns_proposed_plan["interventions"].items()}
            cid = "cand_sns_agent_01"
            sns_actions = cls._build_candidate_actions(
                candidate_id=cid,
                interventions=sns_interventions,
                current_telemetry=current_telemetry,
                rationale=sns_proposed_plan.get("rationale", "Cognitive reasoning from SNS Workbench."),
            )
            candidates.append(
                CandidatePlan(
                    candidate_id=cid,
                    title=sns_proposed_plan.get("title", "SNS 3.0 Cognitive Agent Action Plan"),
                    description=sns_proposed_plan.get("description", "Intervention generated by SNS 3.0 workflow."),
                    proposed_by="SNS_COGNITIVE_AGENT",
                    interventions=sns_interventions,
                    actions=sns_actions,
                    expected_rationale=sns_proposed_plan.get("rationale", "Cognitive reasoning from SNS."),
                )
            )

        # Domain-specific candidate generation (6–8 per fault)
        domain_candidates = cls._domain_candidates(fault_class, cur_oad, cur_chwc, cur_sf, current_telemetry)
        candidates.extend(domain_candidates)

        # Build actions for any candidate that doesn't have them
        for cand in candidates:
            if not cand.actions:
                cand.actions = cls._build_candidate_actions(
                    candidate_id=cand.candidate_id,
                    interventions=cand.interventions,
                    current_telemetry=current_telemetry,
                    rationale=cand.expected_rationale or cand.description,
                )

        # Deduplicate by intervention signature
        candidates = cls._deduplicate(candidates)

        logger.info(f"[CandidateGen] generate_candidates fault={fault_class} → {len(candidates)} candidates")
        return candidates

    # ------------------------------------------------------------------
    # Internal — domain candidate banks (6–8 per fault)
    # ------------------------------------------------------------------

    @classmethod
    def _domain_candidates(
        cls,
        fault_class: str,
        cur_oad: float,
        cur_chwc: float,
        cur_sf: float,
        current_telemetry: Dict[str, float],
    ) -> List[CandidatePlan]:

        if fault_class == FaultClass.DAMPER_STUCK.value:
            return [
                CandidatePlan(
                    candidate_id="cand_ds_min_lock_01",
                    title="Lock Damper Min 10% + Cooling Trim (45%)",
                    description="Force outdoor damper to 10% minimum ventilation and trim chilled water valve to 45%.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"oa_dmpr": 10.0, "chwc_vlv": 45.0},
                    expected_rationale="Eliminates outdoor thermal air ingestion while satisfying ASHRAE 62.1.",
                ),
                CandidatePlan(
                    candidate_id="cand_ds_standard_lock_02",
                    title="Lock Damper Min 20% + Standard Cooling (55%)",
                    description="ASHRAE 62.1 minimum ventilation at 20% with moderate cooling.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"oa_dmpr": 20.0, "chwc_vlv": 55.0},
                    expected_rationale="Standard minimum ventilation with compensatory cooling.",
                ),
                CandidatePlan(
                    candidate_id="cand_ds_moderate_open_03",
                    title="Partial Damper 35% + High Cooling (70%)",
                    description="Moderate outdoor air with aggressive cooling compensation.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"oa_dmpr": 35.0, "chwc_vlv": 70.0},
                    expected_rationale="Partial free cooling with cooling coil compensation.",
                ),
                CandidatePlan(
                    candidate_id="cand_ds_fan_boost_04",
                    title="Fan Boost (85%) + Damper Min (15%)",
                    description="Increase fan speed to compensate for restricted outdoor airflow.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": min(95.0, cur_sf + 8.0), "oa_dmpr": 15.0},
                    expected_rationale="Higher airflow compensates for reduced OA.",
                ),
                CandidatePlan(
                    candidate_id="cand_ds_fan_trim_05",
                    title="Fan Trim (60%) + Valve Override (65%)",
                    description="Reduce fan speed and increase cooling to reach thermal balance.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": max(50.0, cur_sf - 12.0), "chwc_vlv": 65.0},
                    expected_rationale="Lower fan reduces mixing load; higher cooling compensates.",
                ),
                CandidatePlan(
                    candidate_id="cand_ds_aggressive_cool_06",
                    title="Maximum Cooling Override (90%) + Damper Lock (10%)",
                    description="Emergency cooling maximum with outdoor air minimized.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"oa_dmpr": 10.0, "chwc_vlv": 90.0},
                    expected_rationale="Emergency cooling recovery.",
                ),
            ]

        elif fault_class == FaultClass.COI_STUCK.value:
            return [
                CandidatePlan(
                    candidate_id="cand_coi_reset_45_01",
                    title="Cooling Valve Reset 45% + Fan 78%",
                    description="Recalibrate cooling coil valve to 45% and modulate supply fan to 78%.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"chwc_vlv": 45.0, "sf_spd": 78.0},
                    expected_rationale="Restores heat flux balance and prevents coil thermal saturation.",
                ),
                CandidatePlan(
                    candidate_id="cand_coi_moderate_60_02",
                    title="Cooling Valve 60% + OA Lock 15%",
                    description="Moderate valve opening with outdoor air minimized.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"chwc_vlv": 60.0, "oa_dmpr": 15.0},
                    expected_rationale="Moderate cooling with reduced thermal load.",
                ),
                CandidatePlan(
                    candidate_id="cand_coi_high_78_03",
                    title="High Valve 78% + Fan Boost 88%",
                    description="High-demand cooling with increased fan speed for better heat transfer.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"chwc_vlv": 78.0, "sf_spd": 88.0},
                    expected_rationale="Aggressive cooling with high airflow for stuck valve recovery.",
                ),
                CandidatePlan(
                    candidate_id="cand_coi_overdrive_95_04",
                    title="Near-Max Valve Override (95%)",
                    description="Force valve to 95% open to unstick under full differential pressure.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"chwc_vlv": 95.0, "sf_spd": 90.0},
                    expected_rationale="Maximum pressure differential to dislodge valve plug.",
                ),
                CandidatePlan(
                    candidate_id="cand_coi_fan_assist_05",
                    title="Fan Boost 95% to Increase Coil Pressure Drop",
                    description="Maximize fan speed to increase velocity pressure across stuck coil.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": 95.0, "oa_dmpr": 18.0},
                    expected_rationale="Higher airflow creates greater pressure differential to unstick valve.",
                ),
                CandidatePlan(
                    candidate_id="cand_coi_low_load_06",
                    title="Valve 45% + Fan 65% + OA 12%",
                    description="Low-load balanced operation to assess valve response at reduced demand.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"chwc_vlv": 45.0, "sf_spd": 65.0, "oa_dmpr": 12.0},
                    expected_rationale="Reduced system load may allow partial valve movement.",
                ),
                CandidatePlan(
                    candidate_id="cand_coi_max_cool_07",
                    title="Full Chilled Water Valve 100% + OA Lock 15%",
                    description="Maximum chilled water flow with outdoor air lock to pull down zone temperature.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"chwc_vlv": 100.0, "oa_dmpr": 15.0, "sf_spd": 85.0},
                    expected_rationale="Maximum cooling heat flux to restore zone thermal comfort.",
                ),
            ]

        elif fault_class in [FaultClass.COI_LEAKAGE.value, FaultClass.COIL_FOULING_OR_LEAKAGE.value]:
            return [
                CandidatePlan(
                    candidate_id="cand_leak_trim_25_01",
                    title="Deep Valve Reduction (25%) + Fan Trim",
                    description="Trim chilled water valve to 25% and reduce fan to minimize leakage.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"chwc_vlv": 25.0, "sf_spd": max(55.0, cur_sf - 12.0)},
                    expected_rationale="Minimize parasitic subcooling from coil leakage.",
                ),
                CandidatePlan(
                    candidate_id="cand_leak_trim_35_02",
                    title="Conservative Valve Reduction (35%)",
                    description="Trim valve to 35% to reduce leakage while maintaining basic cooling.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"chwc_vlv": 35.0, "oa_dmpr": 18.0},
                    expected_rationale="Balanced leakage control with zone comfort maintenance.",
                ),
                CandidatePlan(
                    candidate_id="cand_leak_moderate_50_03",
                    title="Moderate Valve (50%) + OA Economy",
                    description="Accept controlled leakage at 50% with economizer trim.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"chwc_vlv": 50.0, "oa_dmpr": 20.0},
                    expected_rationale="Maintain adequate cooling despite fouling efficiency loss.",
                ),
                CandidatePlan(
                    candidate_id="cand_leak_fan_reduce_04",
                    title="Fan Reduction (60%) + Valve 30%",
                    description="Reduce fan speed and valve to lower coil differential pressure.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": max(50.0, cur_sf - 15.0), "chwc_vlv": 30.0},
                    expected_rationale="Lower differential pressure reduces leakage rate through coil.",
                ),
                CandidatePlan(
                    candidate_id="cand_leak_setback_05",
                    title="Deep Setback: Fan 45% + Valve 20%",
                    description="Aggressive setback to minimize coil differential pressure completely.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": max(40.0, cur_sf - 25.0), "chwc_vlv": 20.0},
                    expected_rationale="Maximum leakage suppression at minimum system load.",
                ),
                CandidatePlan(
                    candidate_id="cand_leak_oa_isolate_06",
                    title="OA Isolation (15%) + Valve 40%",
                    description="Isolate outdoor air thermal load from fouled coil surface.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"oa_dmpr": 15.0, "chwc_vlv": 40.0},
                    expected_rationale="Reduce total cooling demand on degraded coil surface area.",
                ),
            ]

        elif fault_class == FaultClass.COI_BIAS.value:
            return [
                CandidatePlan(
                    candidate_id="cand_coi_bias_comp_40_01",
                    title="Bias Compensation: Valve 40% + Fan 72%",
                    description="Conservative sensor offset compensation: 40% valve, moderate fan.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"chwc_vlv": 40.0, "sf_spd": 72.0, "oa_dmpr": 20.0},
                    expected_rationale="Conservative bias compensation for +2°C sensor offset.",
                ),
                CandidatePlan(
                    candidate_id="cand_coi_bias_moderate_55_02",
                    title="Moderate Bias Override: Valve 55%",
                    description="Moderate cooling increase to compensate for +3°C bias.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"chwc_vlv": 55.0, "sf_spd": 75.0},
                    expected_rationale="Moderate override for medium sensor drift.",
                ),
                CandidatePlan(
                    candidate_id="cand_coi_bias_high_70_03",
                    title="High Bias Override: Valve 70% + Fan 80%",
                    description="Aggressive cooling to compensate for significant sensor bias.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"chwc_vlv": 70.0, "sf_spd": 80.0},
                    expected_rationale="High override for large sensor offset correction.",
                ),
                CandidatePlan(
                    candidate_id="cand_coi_bias_heavy_85_04",
                    title="Aggressive Cooling Override (85%)",
                    description="Increase cooling valve to 85% for severe sensor bias compensation.",
                    proposed_by="OPERATOR_OVERRIDE",
                    interventions={"chwc_vlv": 85.0, "sf_spd": 85.0, "oa_dmpr": 25.0},
                    expected_rationale="Emergency cooling for significant sensor drift.",
                ),
                CandidatePlan(
                    candidate_id="cand_coi_bias_fan_trim_05",
                    title="Fan Reduction (60%) to Lower False Cooling Demand",
                    description="Reduce airflow to lower the measured-heat-load and reduce false sensor demand.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": max(55.0, cur_sf - 15.0), "chwc_vlv": 50.0},
                    expected_rationale="Lower airflow reduces sensor false-positive cooling demand.",
                ),
                CandidatePlan(
                    candidate_id="cand_coi_bias_oa_lock_06",
                    title="OA Lock 18% + Valve 45%",
                    description="Lock outdoor air to isolate outdoor influence on biased sensor reading.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"oa_dmpr": 18.0, "chwc_vlv": 45.0},
                    expected_rationale="Stabilize mixed air to reduce sensor bias contribution.",
                ),
                CandidatePlan(
                    candidate_id="cand_coi_bias_balanced_07",
                    title="Balanced Override: OA 22%, Valve 60%, Fan 78%",
                    description="Multi-actuator balanced response to sensor bias.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"oa_dmpr": 22.0, "chwc_vlv": 60.0, "sf_spd": 78.0},
                    expected_rationale="Holistic correction across all three control loops.",
                ),
            ]

        elif fault_class == FaultClass.OA_BIAS.value:
            return [
                CandidatePlan(
                    candidate_id="cand_oa_bias_min_15_01",
                    title="OA Fixed Minimum 15% + Valve 38%",
                    description="Bypass biased OA sensor with hardcoded 15% minimum ventilation.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"oa_dmpr": 15.0, "chwc_vlv": 38.0},
                    expected_rationale="Prevent false economizer activation from biased temperature reading.",
                ),
                CandidatePlan(
                    candidate_id="cand_oa_bias_standard_20_02",
                    title="OA Standard Minimum 20% + Fan 70%",
                    description="ASHRAE 62.1 standard minimum OA, bypass biased sensor.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"oa_dmpr": 20.0, "sf_spd": 70.0},
                    expected_rationale="Maintain IAQ compliance without relying on biased sensor.",
                ),
                CandidatePlan(
                    candidate_id="cand_oa_bias_moderate_30_03",
                    title="OA Moderate 30% + Valve 45%",
                    description="Partial outdoor air with compensatory cooling.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"oa_dmpr": 30.0, "chwc_vlv": 45.0},
                    expected_rationale="Compromise between free cooling and sensor error risk.",
                ),
                CandidatePlan(
                    candidate_id="cand_oa_bias_comp_high_55_04",
                    title="High Valve Compensation 55% for OA Under-Read",
                    description="Increase cooling to compensate for OA sensor under-reporting load.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"chwc_vlv": 55.0, "oa_dmpr": 20.0},
                    expected_rationale="Force adequate cooling despite biased OA temperature input.",
                ),
                CandidatePlan(
                    candidate_id="cand_oa_bias_fan_mix_05",
                    title="Fan Boost 82% + OA 20% for Better Mixing",
                    description="Higher fan speed improves mixing, reducing sensor bias impact.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": min(90.0, cur_sf + 10.0), "oa_dmpr": 20.0},
                    expected_rationale="Better mixing dilutes localized sensor temperature error.",
                ),
                CandidatePlan(
                    candidate_id="cand_oa_bias_aggressive_06",
                    title="Aggressive OA Lock 12% + Cooling 65%",
                    description="Emergency outdoor air lock with aggressive compensatory cooling.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"oa_dmpr": 12.0, "chwc_vlv": 65.0},
                    expected_rationale="Maximum isolation from biased OA sensor with cooling recovery.",
                ),
            ]

        elif fault_class == FaultClass.STATIC_PRESSURE_SURGE.value:
            return [
                CandidatePlan(
                    candidate_id="cand_sp_relief_50_01",
                    title="Aggressive Fan Relief to 50%",
                    description="Step down fan from current to 50% to immediately relieve duct overpressure.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": 50.0, "oa_dmpr": 15.0},
                    expected_rationale="Drop duct static below 2.0 in.w.g. rupture limit.",
                ),
                CandidatePlan(
                    candidate_id="cand_sp_moderate_60_02",
                    title="Moderate Fan Reduction to 60%",
                    description="Controlled fan reduction to 60% for measured static relief.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": 60.0, "chwc_vlv": 45.0},
                    expected_rationale="Controlled static pressure reduction with cooling maintained.",
                ),
                CandidatePlan(
                    candidate_id="cand_sp_light_70_03",
                    title="Light Fan Trim to 70%",
                    description="Minimal fan reduction for targeted static relief.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": 70.0, "oa_dmpr": 20.0},
                    expected_rationale="Conservative static pressure reduction.",
                ),
                CandidatePlan(
                    candidate_id="cand_sp_damper_cut_04",
                    title="Damper Restriction to 15% + Fan 58%",
                    description="Combined damper restriction and fan reduction to reduce system pressure.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"oa_dmpr": 15.0, "sf_spd": 58.0},
                    expected_rationale="Reduce inlet and outlet resistance simultaneously.",
                ),
                CandidatePlan(
                    candidate_id="cand_sp_valve_trim_05",
                    title="Chilled Water Valve Trim (40%) to Reduce Coil Resistance",
                    description="Reduce cooling valve to lower hydronic circuit pressure drop.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"chwc_vlv": 40.0, "sf_spd": 62.0},
                    expected_rationale="Lower coil-side resistance contributes to static relief.",
                ),
                CandidatePlan(
                    candidate_id="cand_sp_balanced_06",
                    title="Balanced Relief: Fan 65%, OA 18%, Valve 42%",
                    description="Multi-actuator balanced static pressure relief.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": 65.0, "oa_dmpr": 18.0, "chwc_vlv": 42.0},
                    expected_rationale="Holistic static pressure reduction across all resistance points.",
                ),
            ]

        elif fault_class == FaultClass.FAN_BELT_SLIP.value:
            return [
                CandidatePlan(
                    candidate_id="cand_belt_comp_75_01",
                    title="VFD Slip Compensation 75% + Damper 22%",
                    description="Conservative belt slip compensation: 5% above baseline.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": 75.0, "oa_dmpr": 22.0},
                    expected_rationale="Recover design airflow with minimal slip compensation.",
                ),
                CandidatePlan(
                    candidate_id="cand_belt_moderate_82_02",
                    title="VFD Compensation 82% for Measured Slip Ratio",
                    description="Moderate slip compensation: 10% above slip baseline.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": 82.0, "oa_dmpr": 22.0, "chwc_vlv": 40.0},
                    expected_rationale="Restore 2600 CFM design airflow with measured slip ratio.",
                ),
                CandidatePlan(
                    candidate_id="cand_belt_high_90_03",
                    title="High VFD Override 90% for Severe Slip",
                    description="Aggressive compensation for significant belt degradation.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": 90.0, "chwc_vlv": 42.0},
                    expected_rationale="Force design airflow despite severe belt slip.",
                ),
                CandidatePlan(
                    candidate_id="cand_belt_near_max_95_04",
                    title="Near-Maximum VFD 95% Emergency Recovery",
                    description="Emergency airflow recovery for near-failed belt condition.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": 95.0, "oa_dmpr": 20.0},
                    expected_rationale="Last-resort airflow recovery before mechanical replacement.",
                ),
                CandidatePlan(
                    candidate_id="cand_belt_oa_reduce_05",
                    title="OA Reduction 18% to Lower System Resistance",
                    description="Reduce OA damper to lower external static resistance with belt slip.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"oa_dmpr": 18.0, "sf_spd": 85.0},
                    expected_rationale="Reducing external resistance helps fan overcome slip losses.",
                ),
                CandidatePlan(
                    candidate_id="cand_belt_cool_match_06",
                    title="Fan 85% + Valve 40% to Match Reduced Airflow",
                    description="Match cooling to actual airflow from belt slip.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": 85.0, "chwc_vlv": 40.0},
                    expected_rationale="Right-size cooling to compensate for slip-reduced airflow.",
                ),
            ]

        else:
            # Nominal / Energy Optimization
            return [
                CandidatePlan(
                    candidate_id="cand_energy_tune_01",
                    title="ASHRAE 90.1 Fan Energy Trim (-8%)",
                    description="Trim fan speed by 8% during low-load period.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": max(45.0, cur_sf - 8.0), "oa_dmpr": 20.0},
                    expected_rationale="Harvest 12-18% electrical energy savings.",
                ),
                CandidatePlan(
                    candidate_id="cand_eco_trim_02",
                    title="Deep Fan Setback (-15%) + OA Eco 20%",
                    description="Deep fan trim with economizer optimization.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": max(40.0, cur_sf - 15.0), "oa_dmpr": 20.0},
                    expected_rationale="Maximum fan energy conservation during low occupancy.",
                ),
                CandidatePlan(
                    candidate_id="cand_oa_free_cool_03",
                    title="Economizer Expansion 35% Free Cooling",
                    description="Increase OA damper for maximum free cooling opportunity.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"oa_dmpr": 35.0, "sf_spd": max(50.0, cur_sf - 5.0)},
                    expected_rationale="Exploit favorable outdoor conditions for free cooling.",
                ),
                CandidatePlan(
                    candidate_id="cand_valve_trim_04",
                    title="Chilled Water Valve Trim (-10%)",
                    description="Reduce cooling valve to harvest chiller savings.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"chwc_vlv": max(20.0, cur_chwc - 10.0), "sf_spd": max(50.0, cur_sf - 5.0)},
                    expected_rationale="Reduce chiller plant load and improve COP.",
                ),
                CandidatePlan(
                    candidate_id="cand_balanced_eco_05",
                    title="Balanced Eco: Fan 72%, OA 25%, Valve Trim",
                    description="Multi-actuator balanced energy optimization.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": 72.0, "oa_dmpr": 25.0, "chwc_vlv": max(25.0, cur_chwc - 8.0)},
                    expected_rationale="Holistic energy optimization within comfort constraints.",
                ),
                CandidatePlan(
                    candidate_id="cand_deep_setback_06",
                    title="Deep Setback Mode: All Actuators Minimum",
                    description="Maximum energy conservation during unoccupied period.",
                    proposed_by="GSENSE_ANALYTICAL_ENGINE",
                    interventions={"sf_spd": 40.0, "oa_dmpr": 12.0, "chwc_vlv": 18.0},
                    expected_rationale="Maximum energy savings profile for unoccupied operation.",
                ),
            ]

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @classmethod
    def _build_candidate_actions(
        cls,
        candidate_id: str,
        interventions: Dict[str, float],
        current_telemetry: Dict[str, float],
        rationale: str = "",
    ) -> List[CandidateAction]:
        actions: List[CandidateAction] = []
        for idx, (target, prop_val) in enumerate(interventions.items(), 1):
            cur_val = current_telemetry.get(target, 0.0)
            actions.append(
                CandidateAction(
                    action_id=f"{candidate_id}-ACT-{idx:02d}",
                    target=target,
                    parameter="value",
                    current_value=float(cur_val),
                    proposed_value=float(prop_val),
                    reason=rationale,
                    expected_objective=f"Modulate {target} from {cur_val:.1f}% to {prop_val:.1f}%",
                )
            )
        return actions

    @classmethod
    def _deduplicate(cls, candidates: List[CandidatePlan]) -> List[CandidatePlan]:
        """Remove candidates with identical intervention signatures."""
        seen: set = set()
        unique: List[CandidatePlan] = []
        for cand in candidates:
            sig = frozenset((k, round(v, 1)) for k, v in cand.interventions.items())
            if sig not in seen:
                seen.add(sig)
                unique.append(cand)
        return unique
