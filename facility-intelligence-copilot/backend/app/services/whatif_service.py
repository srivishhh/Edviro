from __future__ import annotations

import logging
from typing import Any

from app.schemas.whatif import (
    WhatIfImpact,
    WhatIfParameterChanges,
    WhatIfParameterState,
    WhatIfPreset,
    WhatIfSimulateRequest,
    WhatIfSimulateResponse,
)

logger = logging.getLogger(__name__)

# Healthy Baseline Operating Range for Commercial Equipment (HVAC / RTU / Chiller)
BASELINE_RANGES = {
    "temperature": (20.0, 26.0),     # °C
    "pressure": (3.0, 4.5),          # bar
    "airflow": (88.0, 100.0),        # % or rated CFM index
    "energy_kw": (5.0, 9.5),         # kW
}

# Standard Reference Assets (mirrors existing repository metadata without DB dependency)
FALLBACK_ASSET_METADATA: dict[str, dict[str, Any]] = {
    "1": {
        "asset_code": "HVAC-001",
        "name": "HVAC-001 (Ground Floor East)",
        "asset_type": "HVAC",
        "default_state": {"temperature": 22.4, "pressure": 3.6, "airflow": 98.0, "energy_kw": 5.2, "health": 98.0},
    },
    "2": {
        "asset_code": "HVAC-002",
        "name": "HVAC-002 (Ground Floor West)",
        "asset_type": "HVAC",
        "default_state": {"temperature": 23.1, "pressure": 3.8, "airflow": 95.0, "energy_kw": 5.5, "health": 95.0},
    },
    "3": {
        "asset_code": "HVAC-003",
        "name": "HVAC-003 (Floor 1 East)",
        "asset_type": "HVAC",
        "default_state": {"temperature": 24.5, "pressure": 3.9, "airflow": 91.0, "energy_kw": 6.8, "health": 92.0},
    },
    "7": {
        "asset_code": "HVAC-007",
        "name": "HVAC-007 (Floor 2 AHU / LBNL RTU)",
        "asset_type": "HVAC",
        "default_state": {"temperature": 29.4, "pressure": 5.6, "airflow": 68.0, "energy_kw": 11.8, "health": 68.0},
    },
    "8": {
        "asset_code": "CHILLER-001",
        "name": "CHILLER-001 (Primary Chiller)",
        "asset_type": "CHILLER",
        "default_state": {"temperature": 7.2, "pressure": 6.2, "airflow": 98.0, "energy_kw": 34.5, "health": 94.0},
    },
    "9": {
        "asset_code": "CHILLER-002",
        "name": "CHILLER-002 (Secondary Chiller)",
        "asset_type": "CHILLER",
        "default_state": {"temperature": 8.1, "pressure": 6.4, "airflow": 92.0, "energy_kw": 38.0, "health": 91.0},
    },
    "10": {
        "asset_code": "HEATPUMP-001",
        "name": "HEATPUMP-001 (Main Heat Pump)",
        "asset_type": "HEATPUMP",
        "default_state": {"temperature": 21.0, "pressure": 4.1, "airflow": 94.0, "energy_kw": 18.2, "health": 96.0},
    },
}

SCENARIO_PRESETS: list[WhatIfPreset] = [
    WhatIfPreset(
        id="normal_operation",
        name="Normal Operation Baseline",
        description="Simulate operating within nominal baseline parameters (clean filters, balanced damper, optimal refrigerant pressure).",
        changes=WhatIfParameterChanges(temperature=23.5, pressure=3.8, airflow=96.0, energy_kw=6.8),
        expected_outcome="Substantial risk reduction, stabilized energy consumption, and high asset health.",
    ),
    WhatIfPreset(
        id="improve_airflow",
        name="Improve Airflow (Filter/Damper Clean)",
        description="Increase airflow velocity to relieve mechanical duct restriction and compressor backpressure.",
        changes=WhatIfParameterChanges(airflow=95.0),
        expected_outcome="Relieves restriction strain, drops discharge pressure, and reduces thermal buildup.",
    ),
    WhatIfPreset(
        id="reduce_pressure",
        name="Condenser Descaling / Head Pressure Reduction",
        description="Reduce excessive refrigerant head pressure down toward nominal design limits (3.8 bar).",
        changes=WhatIfParameterChanges(pressure=3.9),
        expected_outcome="Lowers compressor lift work, reducing electrical demand and mitigating condenser fouling risk.",
    ),
    WhatIfPreset(
        id="energy_optimization",
        name="Energy Optimization Mode",
        description="Optimize temperature setpoint and airflow rate to minimize peak electrical load without sacrificing comfort.",
        changes=WhatIfParameterChanges(temperature=24.0, airflow=92.0, energy_kw=7.2),
        expected_outcome="Reduces energy consumption by up to 30% while maintaining safe operational baselines.",
    ),
    WhatIfPreset(
        id="high_temperature_stress",
        name="High Temperature Stress Test",
        description="Simulate an extreme ambient thermal surge or economizer failure (+5°C supply air temp).",
        changes=WhatIfParameterChanges(temperature=33.5),
        expected_outcome="Spikes thermal risk, triggers secondary compressor power increases, and degrades equipment health.",
    ),
    WhatIfPreset(
        id="airflow_restriction_stress",
        name="Airflow Restriction Severe Fault",
        description="Simulate a severely clogged particulate filter or stuck damper (-30% airflow restriction).",
        changes=WhatIfParameterChanges(airflow=52.0),
        expected_outcome="Severe duct pressure surge, increased fan motor power penalty, and critical operational risk.",
    ),
]


class WhatIfSimulationService:
    """
    Completely isolated, side-effect-free What-If simulation service.
    Guaranteed to NEVER write to database, publish to Kafka, mutate Digital Twin,
    or generate real alarms.
    """

    @classmethod
    def get_presets(cls) -> list[WhatIfPreset]:
        """Returns registered scenario presets."""
        return SCENARIO_PRESETS

    @classmethod
    def resolve_asset_metadata(cls, asset_id_raw: str | int) -> tuple[int, str, str, dict[str, float]]:
        """
        Resolves asset identifier to numeric id, asset code, display name, and baseline reading.
        Safe against non-existent or string asset IDs.
        """
        raw_str = str(asset_id_raw).strip()

        # Check by numeric string
        if raw_str in FALLBACK_ASSET_METADATA:
            meta = FALLBACK_ASSET_METADATA[raw_str]
            return int(raw_str), meta["asset_code"], meta["name"], meta["default_state"]

        # Check by asset code (e.g. "HVAC-007")
        for num_id_str, meta in FALLBACK_ASSET_METADATA.items():
            if meta["asset_code"].upper() == raw_str.upper():
                return int(num_id_str), meta["asset_code"], meta["name"], meta["default_state"]

        # If integer conversion succeeds
        try:
            num_val = int(raw_str)
            num_str = str(num_val)
            if num_str in FALLBACK_ASSET_METADATA:
                meta = FALLBACK_ASSET_METADATA[num_str]
                return num_val, meta["asset_code"], meta["name"], meta["default_state"]
        except ValueError:
            pass

        # Generic safe fallback for unknown assets
        code = f"ASSET-{raw_str}" if not raw_str.startswith("HVAC") and not raw_str.startswith("CHILLER") else raw_str
        default_state = {"temperature": 24.0, "pressure": 4.0, "airflow": 90.0, "energy_kw": 8.0, "health": 85.0}
        return 999, code, f"Equipment ({code})", default_state

    @classmethod
    def get_current_asset_state(cls, asset_id_raw: str | int) -> tuple[str, str, WhatIfParameterState]:
        """
        Retrieves current snapshot of the asset without modifying any live structures.
        Prioritizes real-time telemetry if available in backend in-memory cache,
        falling back to default asset library values.
        """
        num_id, code, name, default_vals = cls.resolve_asset_metadata(asset_id_raw)

        temp = default_vals["temperature"]
        press = default_vals["pressure"]
        flow = default_vals["airflow"]
        energy = default_vals["energy_kw"]
        health = default_vals["health"]

        # Inspect in-memory telemetry library if active
        try:
            from app.api.v1.routes.telemetry import TELEMETRY_LIBRARY, TWIN_LIBRARY
            if num_id in TELEMETRY_LIBRARY and TELEMETRY_LIBRARY[num_id]:
                latest = TELEMETRY_LIBRARY[num_id][-1]
                temp = float(latest.get("temperature", temp))
                press = float(latest.get("pressure", press))
                flow = float(latest.get("airflow", flow))
                energy = float(latest.get("energy_kw", energy))

            if num_id in TWIN_LIBRARY:
                twin_entry = TWIN_LIBRARY[num_id]
                health = float(twin_entry.get("health_score", health))
        except Exception as e:
            logger.debug("Telemetry in-memory cache unavailable: %s", e)

        risk_score, risk_level = cls.calculate_risk(temp, press, flow, energy)

        current_state = WhatIfParameterState(
            temperature=round(temp, 2),
            pressure=round(press, 2),
            airflow=round(flow, 1),
            energy_kw=round(energy, 2),
            health=round(health, 1),
            risk=round(risk_score, 1),
            risk_level=risk_level,
        )

        return code, name, current_state

    @classmethod
    def calculate_risk(cls, temp: float, press: float, flow: float, energy: float) -> tuple[float, str]:
        """
        Calculates a deterministic risk score (0 - 100) based on deviations from normal baseline bounds.
        Categorizes into LOW, MODERATE, HIGH, or CRITICAL.
        """
        total_risk = 0.0

        # Temperature risk penalty (Normal: 20-26°C)
        if temp > 26.0:
            excess_t = temp - 26.0
            total_risk += min(35.0, excess_t * 4.2)
        elif temp < 18.0:
            under_t = 18.0 - temp
            total_risk += min(20.0, under_t * 2.5)

        # Pressure risk penalty (Normal: 3.0-4.5 bar)
        if press > 4.5:
            excess_p = press - 4.5
            total_risk += min(35.0, excess_p * 6.0)
        elif press < 2.5:
            under_p = 2.5 - press
            total_risk += min(25.0, under_p * 8.0)

        # Airflow restriction risk penalty (Normal: 88-100%)
        if flow < 88.0:
            deficit_flow = 88.0 - flow
            total_risk += min(35.0, deficit_flow * 1.1)

        # Energy consumption penalty (Normal: 5-9.5 kW)
        if energy > 9.5:
            excess_energy = energy - 9.5
            total_risk += min(30.0, excess_energy * 2.8)

        final_risk = max(0.0, min(100.0, total_risk))

        if final_risk <= 25.0:
            level = "LOW"
        elif final_risk <= 50.0:
            level = "MODERATE"
        elif final_risk <= 75.0:
            level = "HIGH"
        else:
            level = "CRITICAL"

        return round(final_risk, 1), level

    @classmethod
    def calculate_health(cls, risk: float, temp: float, press: float, flow: float, energy: float) -> float:
        """
        Calculates simulated asset health score (0 - 100).
        Healthy baseline is ~95-100%, degrading proportionally to operational strain.
        """
        base_health = 100.0 - (risk * 0.72)

        # Critical fault multipliers (e.g. near-zero flow or high pressure + high energy)
        if flow < 50.0 and temp > 28.0:
            base_health -= 12.0
        if press > 15.0 and energy > 20.0:  # High-discharge condenser stress
            base_health -= 15.0

        return max(5.0, min(100.0, round(base_health, 1)))

    @classmethod
    def simulate(cls, request: WhatIfSimulateRequest) -> WhatIfSimulateResponse:
        """
        Executes a deterministic What-If simulation on a temporary decoupled state.
        Never modifies live database, live twin, or Kafka stream.
        """
        code, name, current_state = cls.get_current_asset_state(request.asset_id)
        changes = request.changes

        # Temporary simulation values initialized from current state
        sim_temp = current_state.temperature
        sim_press = current_state.pressure
        sim_flow = current_state.airflow
        sim_energy = current_state.energy_kw

        # 1. Apply explicit user inputs
        if changes.temperature is not None:
            sim_temp = changes.temperature
        if changes.pressure is not None:
            sim_press = changes.pressure
        if changes.airflow is not None:
            sim_flow = changes.airflow
        if changes.energy_kw is not None:
            sim_energy = changes.energy_kw

        # 2. Model physical engineering relationships for unconstrained dependent variables
        # If user did not manually fix energy_kw, compute coupled effect of airflow, temperature, and pressure
        if changes.energy_kw is None:
            energy_delta = 0.0

            # A. Airflow effect on fan/compressor work
            if changes.airflow is not None:
                flow_delta = changes.airflow - current_state.airflow
                # Increased airflow reduces restriction penalty, decreasing energy demand
                # Decreased airflow forces fan/compressor to work against backpressure, increasing energy
                energy_delta -= (flow_delta * 0.08)

            # B. Temperature thermal load effect
            if changes.temperature is not None:
                temp_delta = changes.temperature - current_state.temperature
                if changes.temperature > 25.0:
                    energy_delta += (temp_delta * 0.28)
                else:
                    energy_delta += (temp_delta * 0.12)

            # C. Refrigerant head pressure effect
            if changes.pressure is not None:
                press_delta = changes.pressure - current_state.pressure
                energy_delta += (press_delta * 0.35)

            sim_energy = max(2.5, round(current_state.energy_kw + energy_delta, 2))

        # If user did not manually fix pressure, adjust for airflow restriction
        if changes.pressure is None and changes.airflow is not None:
            flow_delta = changes.airflow - current_state.airflow
            # Restriction causes pressure buildup; restoring flow drops pressure toward baseline
            press_adj = - (flow_delta * 0.025)
            sim_press = max(2.0, min(35.0, round(current_state.pressure + press_adj, 2)))

        # 3. Calculate predicted risk and health
        pred_risk, pred_risk_level = cls.calculate_risk(sim_temp, sim_press, sim_flow, sim_energy)
        pred_health = cls.calculate_health(pred_risk, sim_temp, sim_press, sim_flow, sim_energy)

        predicted_state = WhatIfParameterState(
            temperature=round(sim_temp, 2),
            pressure=round(sim_press, 2),
            airflow=round(sim_flow, 1),
            energy_kw=round(sim_energy, 2),
            health=pred_health,
            risk=pred_risk,
            risk_level=pred_risk_level,
        )

        # 4. Calculate comparative quantitative impacts
        energy_diff_kw = round(predicted_state.energy_kw - current_state.energy_kw, 2)
        if current_state.energy_kw > 0:
            energy_diff_pct = round((energy_diff_kw / current_state.energy_kw) * 100.0, 1)
        else:
            energy_diff_pct = 0.0

        health_diff = round(predicted_state.health - current_state.health, 1)
        risk_diff = round(predicted_state.risk - current_state.risk, 1)

        impact = WhatIfImpact(
            energy_change_kw=energy_diff_kw,
            energy_change_percent=energy_diff_pct,
            health_change=health_diff,
            risk_change=risk_diff,
        )

        # 5. Generate high-level assessment, narrative explanation, and recommendations
        assessment = cls._generate_assessment(impact, pred_risk_level)
        explanation = cls._generate_explanation(current_state, predicted_state, impact)
        recommendations = cls._generate_recommendations(current_state, predicted_state, impact)

        return WhatIfSimulateResponse(
            asset_id=code,
            asset_name=name,
            current=current_state,
            predicted=predicted_state,
            impact=impact,
            assessment=assessment,
            recommendations=recommendations,
            explanation=explanation,
            scenario_preset=request.scenario_preset,
            is_simulation=True,
        )

    @staticmethod
    def _generate_assessment(impact: WhatIfImpact, pred_risk_level: str) -> str:
        """Determines categorical summary verdict."""
        if impact.health_change >= 10.0 and impact.risk_change <= -15.0:
            return "Significantly Improved Operating Condition"
        if impact.health_change > 0 and impact.energy_change_percent < 0:
            return "Favorable Efficiency & Health Gain"
        if impact.risk_change >= 20.0 or pred_risk_level == "CRITICAL":
            return "Critical Operational Stress & Elevated Risk"
        if impact.risk_change > 5.0:
            return "Deteriorated Operating Condition"
        if abs(impact.health_change) <= 2.0 and abs(impact.risk_change) <= 2.0:
            return "Nominal / Steady Operating State"
        return "Modified Operational Profile"

    @staticmethod
    def _generate_explanation(
        curr: WhatIfParameterState,
        pred: WhatIfParameterState,
        impact: WhatIfImpact,
    ) -> str:
        """Constructs clear, physics-grounded explanation of simulated causality."""
        reasons: list[str] = []

        # Airflow causality
        if pred.airflow > curr.airflow + 3.0:
            reasons.append(
                f"Increasing airflow from {curr.airflow}% to {pred.airflow}% relieves duct restriction backpressure "
                f"and enhances convective heat exchange."
            )
        elif pred.airflow < curr.airflow - 3.0:
            reasons.append(
                f"Restricting airflow from {curr.airflow}% down to {pred.airflow}% creates aerodynamic throttling, "
                f"forcing fans and compressors to operate against excessive static pressure."
            )

        # Energy causality
        if impact.energy_change_kw < -0.5:
            reasons.append(
                f"Reduced mechanical head loss lowers compressor electrical consumption by {abs(impact.energy_change_kw):.1f} kW "
                f"({abs(impact.energy_change_percent):.1f}% reduction)."
            )
        elif impact.energy_change_kw > 0.5:
            reasons.append(
                f"Higher thermal or mechanical load increases predicted power demand by +{impact.energy_change_kw:.1f} kW "
                f"(+{impact.energy_change_percent:.1f}% increase)."
            )

        # Risk and health outcome
        if impact.risk_change <= -10.0:
            reasons.append(
                f"Operating closer to baseline bounds reduces operational risk by {abs(impact.risk_change):.0f} points, "
                f"restoring asset health score to {pred.health:.0f}%."
            )
        elif impact.risk_change >= 10.0:
            reasons.append(
                f"Exceeding safe baseline parameters elevates operational risk by +{impact.risk_change:.0f} points "
                f"(Risk Level: {pred.risk_level}), depressing predicted health to {pred.health:.0f}%."
            )
        else:
            reasons.append(
                f"Parameters remain stable within typical operating tolerances with predicted health at {pred.health:.0f}%."
            )

        return " ".join(reasons)

    @staticmethod
    def _generate_recommendations(
        curr: WhatIfParameterState,
        pred: WhatIfParameterState,
        impact: WhatIfImpact,
    ) -> list[str]:
        """Produces actionable, non-executing guidance for the facility engineer."""
        recs: list[str] = []

        if pred.airflow > curr.airflow + 5.0 and impact.energy_change_percent < 0:
            recs.append("Clean or replace particulate pre-filters to achieve the simulated airflow recovery.")
            recs.append("Verify economizer outdoor air damper positioning to prevent airflow starvation.")

        if pred.pressure < curr.pressure - 0.5:
            recs.append("Schedule condenser coil cleaning or descaling to permanently reduce discharge head pressure.")

        if impact.energy_change_percent <= -10.0:
            recs.append("Implement proposed setpoint schedule in BMS supervisory controller to realize predicted electrical savings.")

        if pred.temperature > 28.0 or pred.risk >= 60.0:
            recs.append("CAUTION: Simulated parameters place equipment in elevated thermal strain. Avoid sustained operation under this profile.")

        recs.append("Validate physical sensor calibration (temperature thermistors & differential pressure transducers) prior to permanent control changes.")
        recs.append("Decision-support simulation only: Field verification required before adjusting active setpoints.")

        return recs
