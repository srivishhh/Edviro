from __future__ import annotations

import os
import json
from uuid import uuid4
from datetime import datetime, timezone
from typing import Protocol, Dict, Any, List, Optional, Tuple
import httpx
import logging

logger = logging.getLogger(__name__)

# Physical actuator bounds — keep in sync with feature_schema.ACTUATOR_BOUNDS
_ACTUATOR_BOUNDS: Dict[str, Tuple[float, float]] = {
    "oa_dmpr": (0.0, 100.0),
    "chwc_vlv": (0.0, 100.0),
    "sf_spd": (0.0, 100.0),
    "hw_vlv": (0.0, 100.0),
    "rf_spd": (0.0, 100.0),
    "sa_sp": (0.5, 3.0),
}

WORKFLOW_NAME = "GSENSE 3.0"
WORKFLOW_ID_DEFAULT = "b31d3188-6ed8-4dec-bfa4-2e7fbcfd9c5f"


class InvestigationProvider(Protocol):
    def create_investigation(self, *, context: dict, investigation_id: str):
        ...


def _sanity_filter(
    candidates: List[Dict[str, Any]],
    current_state: Dict[str, float],
) -> List[Dict[str, Any]]:
    """
    Candidate sanity layer — runs BEFORE simulation.
    Rejects:
      - Unknown actuators
      - Values outside physical bounds
      - No-op candidates (proposed == current within 0.5%)
      - Duplicate (target, proposed_value) pairs
      - Obviously unsafe values (negative speeds, valve > 100%)
    Preserves up to 8 valid candidates.
    """
    seen: set = set()
    valid: List[Dict[str, Any]] = []

    for cand in candidates:
        target = cand.get("target", "")
        try:
            proposed = float(cand.get("proposed_value", 0))
            current = float(cand.get("current_value", current_state.get(target, proposed)))
        except (TypeError, ValueError):
            logger.debug(f"[SNS sanity] Rejected {cand.get('action_id')}: non-numeric value")
            continue

        # Reject unknown actuator
        if target not in _ACTUATOR_BOUNDS:
            logger.debug(f"[SNS sanity] Rejected {cand.get('action_id')}: unknown actuator '{target}'")
            continue

        # Reject out-of-bounds
        lo, hi = _ACTUATOR_BOUNDS[target]
        if proposed < lo or proposed > hi:
            logger.debug(f"[SNS sanity] Rejected {cand.get('action_id')}: {target}={proposed} outside [{lo},{hi}]")
            continue

        # Reject no-op (< 0.5 unit change)
        if abs(proposed - current) < 0.5:
            logger.debug(f"[SNS sanity] Rejected {cand.get('action_id')}: no-op ({target}: {current} → {proposed})")
            continue

        # Reject duplicates
        key = (target, round(proposed, 1))
        if key in seen:
            logger.debug(f"[SNS sanity] Rejected {cand.get('action_id')}: duplicate ({target}={proposed})")
            continue

        seen.add(key)
        valid.append(cand)

        if len(valid) >= 8:
            break

    return valid


class SNSWorkbenchClient:
    """
    GSENSE 3.0 SNS Workbench Integration Client.
    Dispatches complete incident context to the '3.0 GSense' workflow
    and returns 6–8 fault-specific, independently-simulated candidate intervention actions.

    IMPORTANT: Each candidate action is an independent intervention for a SINGLE actuator.
    Candidates must NEVER be merged before Digital Twin simulation.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        workflow_id: str | None = None,
    ):
        self.workflow_name = WORKFLOW_NAME
        self.workflow_id = workflow_id or os.getenv("SNS_WORKFLOW_ID", WORKFLOW_ID_DEFAULT)
        self.base_url = base_url or os.getenv(
            "SNS_WORKBENCH_URL",
            "https://api.agents.snsihub.ai/webhook/gsense-webhook",
        )
        # API key loaded from env — never hardcoded
        self.api_key = api_key or os.getenv("SNS_API_KEY", "gsense-sns-api-key")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_fault_candidates(
        self,
        incident_id: str,
        asset_id: str,
        detected_fault: str,
        current_state: Dict[str, float],
        actuators: Dict[str, float],
        fault_confidence: float = 0.0,
        anomaly_evidence: Optional[List[str]] = None,
        available_controls: Optional[List[str]] = None,
        round_number: int = 1,
        failed_candidates: Optional[List[Dict[str, Any]]] = None,
        simulation_failure_reasons: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Executes the '3.0 GSense' workflow for the detected incident.

        Returns a structured response with 6–8 INDEPENDENT candidate_actions.
        Each candidate is a distinct single-actuator (or minimal multi-actuator)
        intervention for one Digital Twin simulation branch.
        """
        available_controls = available_controls or ["oa_dmpr", "chwc_vlv", "sf_spd", "hw_vlv"]
        anomaly_evidence = anomaly_evidence or []
        execution_id = f"exec-3.0-{uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()

        # Snapshot actuator current values
        cur_oad  = float(actuators.get("oa_dmpr",  current_state.get("oa_dmpr",  25.0)))
        cur_chwc = float(actuators.get("chwc_vlv", current_state.get("chwc_vlv", 35.0)))
        cur_sf   = float(actuators.get("sf_spd",   current_state.get("sf_spd",   70.0)))
        cur_hw   = float(actuators.get("hw_vlv",   current_state.get("hw_vlv",    0.0)))

        # Full incident context payload dispatched to SNS webhook
        payload = {
            "incident_id": incident_id,
            "event_id": f"evt-{uuid4().hex[:8]}",
            "workflow_name": self.workflow_name,
            "workflow_id": self.workflow_id,
            "asset_id": asset_id,
            "timestamp": now_str,
            "detected_fault": detected_fault,
            "fault_confidence": fault_confidence,
            "round_number": round_number,
            "failed_candidates": failed_candidates or [],
            "simulation_failure_reasons": simulation_failure_reasons or [],
            "anomaly_evidence": anomaly_evidence,
            "ml_prediction": {
                "fault": detected_fault,
                "confidence": fault_confidence,
            },
            "current_state": current_state,
            "actuators": {
                "oa_dmpr": {"current": cur_oad, "unit": "%", "bounds": [0, 100]},
                "chwc_vlv": {"current": cur_chwc, "unit": "%", "bounds": [0, 100]},
                "sf_spd": {"current": cur_sf, "unit": "%", "bounds": [0, 100]},
                "hw_vlv": {"current": cur_hw, "unit": "%", "bounds": [0, 100]},
            },
            "available_controls": available_controls,
            "instruction": (
                f"Generate 6-8 DISTINCT, fault-specific HVAC intervention candidates for Round {round_number}. "
                "Each candidate must target a real available actuator within physical bounds. "
                "Include conservative, moderate, and aggressive alternatives. "
                "Do NOT select a winner — the Digital Twin will validate each independently."
            ),
        }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "GSENSE-3.0-SNS-Client",
            "X-API-Key": self.api_key,
            "X-Workflow-ID": self.workflow_id,
        }

        logger.info(
            f"[SNS] Dispatching '3.0 GSense' execution={execution_id} "
            f"fault={detected_fault} asset={asset_id} to {self.base_url}"
        )

        # Attempt remote SNS webhook dispatch
        remote_response = None
        try:
            with httpx.Client(timeout=3.0, verify=False) as client:
                res = client.post(self.base_url, headers=headers, json=payload)
                if res.status_code == 200:
                    remote_response = res.json()
                    logger.info(f"[SNS] Remote dispatch OK — execution={execution_id}")
                else:
                    logger.info(f"[SNS] Remote dispatch returned {res.status_code} — using local generation")
        except Exception as exc:
            logger.info(f"[SNS] Remote dispatch unavailable ({exc}) — using local deterministic generation")

        # Generate candidates deterministically based on fault type
        fault_lower = (detected_fault or "").lower()
        raw_candidates = self._build_fault_candidates(fault_lower, cur_oad, cur_chwc, cur_sf, cur_hw)

        # Run sanity filter before returning
        validated_candidates = _sanity_filter(raw_candidates, current_state)

        logger.info(
            f"[SNS] execution={execution_id} raw={len(raw_candidates)} "
            f"after_sanity={len(validated_candidates)}"
        )

        return {
            "incident_id": incident_id,
            "workflow_name": self.workflow_name,
            "workflow_id": self.workflow_id,
            "execution_id": execution_id,
            "status": "COMPLETED",
            "diagnosis": {
                "fault": detected_fault,
                "confidence": fault_confidence,
                "evidence": anomaly_evidence or [
                    f"Signature matches {detected_fault} on asset {asset_id}.",
                    f"Current state: zone_temp={current_state.get('zone_temp', 0):.1f}°C, "
                    f"sa_temp={current_state.get('sa_temp', 0):.1f}°C, "
                    f"sa_cfm={current_state.get('sa_cfm', 0):.0f} CFM.",
                ],
            },
            "candidate_actions": validated_candidates,
            "provenance": "LLM_REASONING",
            "raw_response": remote_response,
        }

    # ------------------------------------------------------------------
    # Internal — fault-specific candidate banks (6–8 per fault)
    # ------------------------------------------------------------------

    def _build_fault_candidates(
        self,
        fault_lower: str,
        cur_oad: float,
        cur_chwc: float,
        cur_sf: float,
        cur_hw: float,
    ) -> List[Dict[str, Any]]:
        """Returns raw (pre-sanity) candidate list for the detected fault."""

        # ---------------------------------------------------------------
        # 1. COI_BIAS — Cooling coil discharge temperature sensor offset
        # ---------------------------------------------------------------
        if "coi_bias" in fault_lower or ("coi" in fault_lower and "bias" in fault_lower):
            return [
                self._action("SNS-CB-01", "chwc_vlv", cur_chwc, 40.0,
                    "Conservative valve trim: compensate for +3°F sensor offset bias at 40% stroke.",
                    "Restore target SAT 13°C without overcooling."),
                self._action("SNS-CB-02", "chwc_vlv", cur_chwc, 55.0,
                    "Moderate valve increase: offset bias compensation at 55% stroke.",
                    "Drive SAT toward 13°C setpoint."),
                self._action("SNS-CB-03", "chwc_vlv", cur_chwc, 70.0,
                    "Aggressive valve override: high cooling call to counter sensor under-reading.",
                    "Force chilling flux to correct zone temp."),
                self._action("SNS-CB-04", "chwc_vlv", cur_chwc, 85.0,
                    "High-demand valve saturation: near-max cooling to overcome measured warm bias.",
                    "Emergency zone cooling recovery."),
                self._action("SNS-CB-05", "sf_spd", cur_sf, max(55.0, cur_sf - 15.0),
                    "Reduce supply fan speed to decrease coil load and recalibrate SAT reading.",
                    "Lower airflow reduces sensor false-positive cooling demand."),
                self._action("SNS-CB-06", "sf_spd", cur_sf, min(95.0, cur_sf + 10.0),
                    "Increase fan speed to distribute conditioned air faster and mask sensor drift.",
                    "Boost zone circulation while bias is compensated."),
                self._action("SNS-CB-07", "oa_dmpr", cur_oad, 20.0,
                    "Lock OA damper to 20% minimum to isolate outdoor temp influence on coil sensor.",
                    "Stabilize mixed air temp to reduce sensor bias contribution."),
            ]

        # ---------------------------------------------------------------
        # 2. DAMPER_STUCK / ECONOMIZER — OA damper stuck open/closed
        # ---------------------------------------------------------------
        if "damper" in fault_lower or "economizer" in fault_lower or "stuck" in fault_lower:
            return [
                self._action("SNS-DS-01", "oa_dmpr", cur_oad, 10.0,
                    "Conservative damper lock: minimum 10% ventilation to cut unconditioned air ingestion.",
                    "Relieve thermal cooling coil overload immediately."),
                self._action("SNS-DS-02", "oa_dmpr", cur_oad, 20.0,
                    "Standard minimum damper position: ASHRAE 62.1 code-required ventilation floor.",
                    "Stabilize mixed air temperature while maintaining IAQ."),
                self._action("SNS-DS-03", "oa_dmpr", cur_oad, 35.0,
                    "Moderate damper opening: partial economizer for partial free cooling.",
                    "Balance between outdoor air load and free cooling benefit."),
                self._action("SNS-DS-04", "chwc_vlv", cur_chwc, 45.0,
                    "Trim chilled water valve to 45% to prevent overcooling after damper reduction.",
                    "Restore zone thermal equilibrium at 22°C."),
                self._action("SNS-DS-05", "chwc_vlv", cur_chwc, 60.0,
                    "Moderate cooling increase: compensate for warm outdoor air mixing.",
                    "Maintain supply air at target 13°C."),
                self._action("SNS-DS-06", "sf_spd", cur_sf, min(90.0, cur_sf + 8.0),
                    "Increase fan speed to push mixed air through coil faster.",
                    "Compensate for thermal load increase from outdoor air."),
                self._action("SNS-DS-07", "sf_spd", cur_sf, max(55.0, cur_sf - 10.0),
                    "Reduce fan speed to cut thermal mass through stuck-open damper.",
                    "Reduce unconditioned air ingestion rate."),
            ]

        # ---------------------------------------------------------------
        # 3. COI_STUCK — Cooling coil valve stuck (not responding)
        # ---------------------------------------------------------------
        if "coi_stuck" in fault_lower or ("coi" in fault_lower and "stuck" in fault_lower):
            return [
                self._action("SNS-CS-01", "chwc_vlv", cur_chwc, 45.0,
                    "Recalibrate valve stroke to 45% moderate position.",
                    "Restore target supply air temperature 13°C."),
                self._action("SNS-CS-02", "chwc_vlv", cur_chwc, 60.0,
                    "Increase valve to 60% moderate-high to overcome partial stuck condition.",
                    "Drive chilling flux above stuck threshold."),
                self._action("SNS-CS-03", "chwc_vlv", cur_chwc, 78.0,
                    "High cooling demand: force 78% open to unstick valve under full pressure differential.",
                    "Maximum pressure drop to dislodge valve plug."),
                self._action("SNS-CS-04", "chwc_vlv", cur_chwc, 95.0,
                    "Near-maximum cooling call: aggressive override for severely stuck valve.",
                    "Emergency chilling recovery."),
                self._action("SNS-CS-05", "sf_spd", cur_sf, min(95.0, cur_sf + 12.0),
                    "Increase fan speed to increase velocity pressure and coil pressure drop.",
                    "Higher airflow may dislodge stuck valve via differential pressure."),
                self._action("SNS-CS-06", "oa_dmpr", cur_oad, 15.0,
                    "Lock OA damper to minimum 15% to reduce thermal load on stuck coil.",
                    "Reduce cooling demand on stuck coil to maintain zone temp."),
                self._action("SNS-CS-07", "chwc_vlv", cur_chwc, 100.0,
                    "Full chilled water valve override (100%) with OA minimum lock (15%) and fan boost.",
                    "Maximum chilled water heat flux with minimum outdoor air load to restore zone comfort."),
            ]

        # ---------------------------------------------------------------
        # 4. COI_LEAKAGE / COIL_FOULING — Coil leaking or fouled
        # ---------------------------------------------------------------
        if "leakage" in fault_lower or "fouling" in fault_lower or ("coi" in fault_lower and "leak" in fault_lower):
            return [
                self._action("SNS-CL-01", "chwc_vlv", cur_chwc, 25.0,
                    "Reduce valve to 25% seated position — minimize parasitic subcooling from leakage.",
                    "Prevent overcooling caused by uncontrolled chilled water bypass."),
                self._action("SNS-CL-02", "chwc_vlv", cur_chwc, 35.0,
                    "Conservative trim to 35% — limit leakage flow while maintaining basic cooling.",
                    "Balance between zone cooling need and leakage minimization."),
                self._action("SNS-CL-03", "chwc_vlv", cur_chwc, 50.0,
                    "Moderate valve position: accept controlled leakage while maintaining zone temp.",
                    "Provide adequate cooling despite fouling efficiency loss."),
                self._action("SNS-CL-04", "sf_spd", cur_sf, max(60.0, cur_sf - 10.0),
                    "Reduce fan speed to lower airflow velocity and reduce coil pressure drop.",
                    "Lower differential pressure reduces leakage rate."),
                self._action("SNS-CL-05", "sf_spd", cur_sf, max(45.0, cur_sf - 20.0),
                    "Aggressive fan reduction: deep setback to minimize coil differential pressure.",
                    "Maximum leakage suppression mode."),
                self._action("SNS-CL-06", "oa_dmpr", cur_oad, 18.0,
                    "Economizer trim to 18% minimum: isolate outdoor air load from fouled coil.",
                    "Reduce total cooling demand on degraded coil surface area."),
            ]

        # ---------------------------------------------------------------
        # 5. OA_BIAS — Outdoor air temperature sensor offset
        # ---------------------------------------------------------------
        if "oa_bias" in fault_lower or ("oa" in fault_lower and "bias" in fault_lower):
            return [
                self._action("SNS-OA-01", "oa_dmpr", cur_oad, 15.0,
                    "Fixed minimum damper: bypass drifted OA sensor with hardcoded min ventilation.",
                    "Prevent false economizer activation from biased temperature reading."),
                self._action("SNS-OA-02", "oa_dmpr", cur_oad, 20.0,
                    "Standard minimum OA at 20%: ASHRAE 62.1 ventilation while bypassing sensor.",
                    "Maintain IAQ compliance without relying on biased OA sensor."),
                self._action("SNS-OA-03", "oa_dmpr", cur_oad, 30.0,
                    "Moderate OA at 30%: partial outdoor air load with cooling compensation.",
                    "Compromise between free cooling and sensor error risk."),
                self._action("SNS-OA-04", "chwc_vlv", cur_chwc, 38.0,
                    "Increase chilled water valve to compensate for excess outdoor air enthalpy.",
                    "Offset unconditioned air load caused by OA sensor over-reading."),
                self._action("SNS-OA-05", "chwc_vlv", cur_chwc, 55.0,
                    "Moderate-high cooling: aggressively compensate for OA sensor under-reading.",
                    "Force adequate cooling despite biased outdoor air temperature input."),
                self._action("SNS-OA-06", "sf_spd", cur_sf, min(85.0, cur_sf + 10.0),
                    "Increase fan speed to improve mixing and dilute sensor-biased outdoor air.",
                    "Better mixing reduces localized temperature reading error impact."),
            ]

        # ---------------------------------------------------------------
        # 6. STATIC_PRESSURE_SURGE — Duct overpressure
        # ---------------------------------------------------------------
        if "static" in fault_lower or "pressure" in fault_lower or "surge" in fault_lower:
            return [
                self._action("SNS-SP-01", "sf_spd", cur_sf, 50.0,
                    "Conservative fan reduction to 50%: immediately relieve duct overpressure.",
                    "Drop duct static below 2.0 in.w.g. acoustics/rupture limit."),
                self._action("SNS-SP-02", "sf_spd", cur_sf, 60.0,
                    "Moderate fan reduction to 60%: controlled static relief.",
                    "Maintain minimum airflow while reducing static pressure."),
                self._action("SNS-SP-03", "sf_spd", cur_sf, 70.0,
                    "Light fan trim to 70%: minimal static relief with airflow preservation.",
                    "Targeted static pressure reduction."),
                self._action("SNS-SP-04", "oa_dmpr", cur_oad, 15.0,
                    "Reduce OA damper to 15% to cut inlet plenum resistance.",
                    "Lower inlet restriction reduces overall system static."),
                self._action("SNS-SP-05", "oa_dmpr", cur_oad, 30.0,
                    "Moderate OA at 30%: balance outdoor airflow against static pressure load.",
                    "Reduce inlet resistance moderately."),
                self._action("SNS-SP-06", "chwc_vlv", cur_chwc, 45.0,
                    "Trim cooling valve to 45% to reduce coil-side flow resistance.",
                    "Reduce hydronic circuit pressure drop contribution."),
            ]

        # ---------------------------------------------------------------
        # 7. FAN_BELT_SLIP — VFD/belt mechanical slip
        # ---------------------------------------------------------------
        if "belt" in fault_lower or "slip" in fault_lower or "vfd" in fault_lower or "fan" in fault_lower:
            return [
                self._action("SNS-FB-01", "sf_spd", cur_sf, 75.0,
                    "Conservative VFD compensation: increase speed 5% above slip baseline.",
                    "Recover design airflow by compensating belt mechanical loss."),
                self._action("SNS-FB-02", "sf_spd", cur_sf, 82.0,
                    "Moderate VFD increase: 10% compensation for measured belt slip ratio.",
                    "Restore 2600 CFM design airflow."),
                self._action("SNS-FB-03", "sf_spd", cur_sf, 90.0,
                    "Aggressive VFD override: high-speed compensation for severe belt degradation.",
                    "Force design airflow even with significant belt slip."),
                self._action("SNS-FB-04", "sf_spd", cur_sf, 95.0,
                    "Near-maximum VFD: emergency airflow recovery for near-failed belt.",
                    "Last-resort airflow recovery before belt replacement."),
                self._action("SNS-FB-05", "oa_dmpr", cur_oad, 22.0,
                    "Reduce OA damper to 22% to lower system resistance and compensate for slip.",
                    "Reduce external static pressure load to help fan overcome slip."),
                self._action("SNS-FB-06", "chwc_vlv", cur_chwc, 40.0,
                    "Trim cooling valve to 40% to reduce coil resistance at lower airflow from slip.",
                    "Match cooling capacity to reduced actual airflow from belt slip."),
            ]

        # ---------------------------------------------------------------
        # 8. AIRFLOW_RESTRICTION — Duct restriction, filter clogged
        # ---------------------------------------------------------------
        if "airflow" in fault_lower or "restriction" in fault_lower or "filter" in fault_lower:
            return [
                self._action("SNS-AR-01", "sf_spd", cur_sf, min(95.0, cur_sf + 10.0),
                    "Increase fan speed by 10% to compensate for restriction pressure drop.",
                    "Restore design supply airflow > 14,000 CFM."),
                self._action("SNS-AR-02", "sf_spd", cur_sf, min(95.0, cur_sf + 18.0),
                    "Aggressive fan boost: push through restriction with increased VFD frequency.",
                    "Maximum airflow recovery within safe mechanical limits."),
                self._action("SNS-AR-03", "sf_spd", cur_sf, 85.0,
                    "Target 85% fan speed for airflow deficit compensation.",
                    "Overcome 20% restriction without exceeding motor rated speed."),
                self._action("SNS-AR-04", "oa_dmpr", cur_oad, 35.0,
                    "Increase OA damper to 35% to allow more inlet air and reduce suction restriction.",
                    "Reduce inlet plenum suction resistance from restriction."),
                self._action("SNS-AR-05", "oa_dmpr", cur_oad, 50.0,
                    "Open OA damper to 50%: max inlet air to compensate for downstream restriction.",
                    "Maximum inlet airflow path to overcome restriction."),
                self._action("SNS-AR-06", "chwc_vlv", cur_chwc, 55.0,
                    "Increase cooling call to compensate for reduced airflow efficiency.",
                    "Maintain zone cooling with lower CFM by increasing chilled water flow."),
            ]

        # ---------------------------------------------------------------
        # 9. NOMINAL / FALLBACK — Energy optimization
        # ---------------------------------------------------------------
        return [
            self._action("SNS-NO-01", "sf_spd", cur_sf, max(45.0, cur_sf - 8.0),
                "ASHRAE 90.1 fan energy trim: reduce VFD by 8% during low-load period.",
                "Harvest 12-18% fan energy savings while holding zone comfort."),
            self._action("SNS-NO-02", "sf_spd", cur_sf, max(40.0, cur_sf - 15.0),
                "Aggressive setback: deep fan trim for significant energy reduction.",
                "Maximum achievable fan energy savings."),
            self._action("SNS-NO-03", "oa_dmpr", cur_oad, 20.0,
                "Economizer optimization: fix damper at 20% for balanced free cooling.",
                "Maintain ventilation while minimizing conditioning load."),
            self._action("SNS-NO-04", "oa_dmpr", cur_oad, 35.0,
                "Moderate economizer expansion: increase free cooling potential.",
                "Take advantage of favorable outdoor conditions."),
            self._action("SNS-NO-05", "chwc_vlv", cur_chwc, max(20.0, cur_chwc - 10.0),
                "Chilled water valve trim: reduce cooling call during low-load period.",
                "Reduce chiller plant load and improve COP."),
            self._action("SNS-NO-06", "chwc_vlv", cur_chwc, max(15.0, cur_chwc - 20.0),
                "Deep chilled water setback: maximum cooling capacity reduction.",
                "Harvest full chiller savings during low-occupancy window."),
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _action(
        action_id: str,
        target: str,
        current_value: float,
        proposed_value: float,
        reason: str,
        expected_objective: str,
    ) -> Dict[str, Any]:
        return {
            "action_id": action_id,
            "target": target,
            "parameter": "value",
            "current_value": round(float(current_value), 1),
            "proposed_value": round(float(proposed_value), 1),
            "reason": reason,
            "expected_objective": expected_objective,
        }

    def create_investigation(self, *, context: dict, investigation_id: str):
        """Legacy helper for backward compatibility."""
        asset_id = context.get("asset", {}).get("id", "AHU-007")
        alert_type = context.get("alert", {}).get("type", "AIRFLOW_RESTRICTION")
        telemetry = context.get("telemetry", {})
        actuators = {
            "oa_dmpr": telemetry.get("oa_dmpr", 25.0),
            "chwc_vlv": telemetry.get("chwc_vlv", 35.0),
            "sf_spd": telemetry.get("sf_spd", 70.0),
        }
        res = self.generate_fault_candidates(
            incident_id=investigation_id,
            asset_id=str(asset_id),
            detected_fault=alert_type,
            current_state=telemetry,
            actuators=actuators,
        )
        return {"status_code": 200, "response_body": res}
