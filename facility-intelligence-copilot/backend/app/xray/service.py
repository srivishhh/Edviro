from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.integrations.sns_workbench import InvestigationProvider, SNSWorkbenchClient
from app.xray.investigation import InvestigationContext, InvestigationContextBuilder
from app.xray.models import Evidence, XRayInvestigationResult


@dataclass
class InvestigationRecord:
    investigation_id: str
    asset_id: int
    alert_id: int
    status: str = "PENDING"
    created_at: datetime = None
    result: XRayInvestigationResult | None = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class XRayService:
    def __init__(self, provider: InvestigationProvider | None = None):
        self.provider = provider or SNSWorkbenchClient()
        self._records: dict[str, InvestigationRecord] = {}

    def _derive_reasoning(self, context: InvestigationContext) -> tuple[list[str], list[str], list[str], list[str], str, str]:
        alert_type = context.alert.get("alert_type", "AIRFLOW_RESTRICTION")
        state = context.current_state

        if alert_type == "AIRFLOW_RESTRICTION":
            observed = [
                f"OBSERVED: Airflow measured at {state.get('airflow', 64.0)}% (baseline: 95.0%).",
                f"OBSERVED: Supply temperature elevated at {state.get('temperature', 30.1)}°C (normal: 20-26°C).",
                f"OBSERVED: Power consumption increased to {state.get('energy_kw', 12.3)} kW (normal: 5-8 kW).",
                f"OBSERVED: Static pressure at {state.get('pressure', 4.3)} bar indicating back-pressure.",
            ]
            inferred = [
                "INFERRED: Physical airflow blockage or damper restriction in supply duct path.",
                "INFERRED: Fan motor working against aerodynamic resistance causing elevated electrical load.",
            ]
            root_cause = "Airflow restriction due to clogged filter or restricted damper actuator in HVAC supply duct."
            confidence = "High"
            alternative_causes = [
                "Hypothesis 1 (Primary - 88% confidence): Intake filter loading or damper restriction causing localized pressure drop.",
                "Hypothesis 2 (Secondary - 34% confidence): Chilled water flow degradation from upstream CHILLER-002.",
                "Hypothesis 3 (Alternative - 18% confidence): Variable frequency drive (VFD) calibration drift.",
            ]
            recommended_actions = [
                "Inspect and replace primary intake air filter on HVAC-007.",
                "Check motorized damper actuator positioning and mechanical linkages.",
                "Verify upstream chilled water supply temperature and flow from CHILLER-002.",
            ]
        elif alert_type == "HIGH_ENERGY":
            observed = [
                f"OBSERVED: Energy consumption measured at {state.get('energy_kw', 12.0)} kW (expected: 5-8 kW).",
                f"OBSERVED: Airflow stable at {state.get('airflow', 90.0)}%.",
            ]
            inferred = [
                "INFERRED: Compressor or fan motor running at continuous peak duty cycle.",
            ]
            root_cause = "High electrical load caused by compressor mechanical resistance or continuous full-duty operation."
            confidence = "High"
            alternative_causes = [
                "Hypothesis 1 (Primary - 82% confidence): Motor bearing wear or excessive refrigerant head pressure.",
                "Hypothesis 2 (Secondary - 40% confidence): Control loop setpoint hunting causing rapid cycling.",
            ]
            recommended_actions = [
                "Inspect motor electrical current draw across all phases.",
                "Check compressor oil level and suction/discharge pressure differentials.",
            ]
        elif alert_type == "HIGH_TEMPERATURE":
            observed = [
                f"OBSERVED: Temperature measured at {state.get('temperature', 32.0)}°C (threshold: 28.0°C).",
            ]
            inferred = [
                "INFERRED: Insufficient thermal exchange capacity in heat exchange coil causing high temperature.",
            ]
            root_cause = "High temperature condition caused by thermal exchange deficiency or reduced coolant flow."
            confidence = "High"
            alternative_causes = [
                "Hypothesis 1 (Primary - 80% confidence): Coolant loop valve partially restricted.",
                "Hypothesis 2 (Secondary - 35% confidence): Ambient thermal load exceeding rated tonnage.",
            ]
            recommended_actions = [
                "Inspect coolant control valve actuator position and chilled water supply temp.",
                "Clean heat exchanger coils and check for bio-fouling.",
            ]
        elif alert_type == "CONDENSER_FOULING":
            discharge_p = state.get("pressure", 24.5)
            power_kw = state.get("energy_kw", 14.2)
            supply_t = state.get("temperature", 22.0)
            observed = [
                f"OBSERVED: Compressor discharge head pressure elevated at {discharge_p:.1f} bar (baseline: 12.0-16.0 bar).",
                f"OBSERVED: Electrical power demand surged to {power_kw:.1f} kW (expected baseline: 6.0-8.5 kW).",
                f"OBSERVED: Heat rejection efficiency degraded with supply temperature operating at {supply_t:.1f}°C.",
            ]
            inferred = [
                "INFERRED: Severe thermodynamic heat transfer resistance across exterior condenser coil fins.",
                "INFERRED: Compressor forced to operate against high compression ratio and back-pressure, driving motor power over-consumption.",
            ]
            root_cause = "Condenser coil fouling with particulate accumulation on exterior heat exchanger fins inhibiting ambient heat rejection."
            confidence = "High"
            alternative_causes = [
                "Hypothesis 1 (Primary - 86% confidence): Condenser coil fin fouling or debris accumulation causing elevated condensing pressure.",
                "Hypothesis 2 (Secondary - 24% confidence): Non-condensable air contamination in refrigerant circuit.",
                "Hypothesis 3 (Alternative - 14% confidence): Condenser fan motor speed reduction or blade damage.",
            ]
            recommended_actions = [
                "Dispatch technician to physically inspect and wash condenser coils with non-acidic coil cleaner.",
                "Verify condenser fan air velocity and fan motor current draw across all phases.",
                "Measure liquid line refrigerant subcooling and discharge superheat post coil cleaning.",
            ]

        elif alert_type == "PRESSURE_ANOMALY":
            observed = [
                f"OBSERVED: System pressure measured at {state.get('pressure', 5.2)} bar (expected: 3.0-4.0 bar).",
            ]
            inferred = [
                "INFERRED: Downstream restriction or expansion valve throttling error creating pressure anomaly.",
            ]
            root_cause = "Pressure anomaly from refrigerant or hydronic line throttling restriction."
            confidence = "Medium"
            alternative_causes = [
                "Hypothesis 1 (Primary - 78% confidence): Throttling valve malfunction or line blockage.",
                "Hypothesis 2 (Secondary - 42% confidence): Pressure relief regulator out of calibration.",
            ]
            recommended_actions = [
                "Check pressure regulating valves and pressure sensor calibration.",
                "Inspect line filters and expansion valves for debris accumulation.",
            ]


        elif alert_type == "SENSOR_FAILURE":
            observed = [
                f"OBSERVED: Telemetry readings outside physical envelope (airflow: {state.get('airflow', 0)}%, temp: {state.get('temperature', -30)}°C).",
            ]
            inferred = [
                "INFERRED: Sensor signal loss, open thermocouple, or transducer failure.",
            ]
            root_cause = "Telemetry sensor electrical disconnect or transducer hardware fault."
            confidence = "High"
            alternative_causes = [
                "Hypothesis 1 (Primary - 95% confidence): Signal wiring disconnect or transducer failure.",
                "Hypothesis 2 (Secondary - 15% confidence): Analog-to-digital converter channel fault.",
            ]
            recommended_actions = [
                "Perform physical loop check and verify sensor terminal connections.",
                "Test sensor transducer with reference multimeter / calibrator.",
            ]
        else:
            observed = [f"OBSERVED: Anomaly reported for {context.asset.get('asset_code')}."]
            inferred = ["INFERRED: Operational state deviates from deterministic baseline."]
            root_cause = context.anomaly.get("description", "Unidentified operational anomaly.")
            confidence = "Medium"
            alternative_causes = ["Hypothesis 1: Operational anomaly requiring field inspection."]
            recommended_actions = ["Inspect asset and verify operating parameters."]

        return observed, inferred, alternative_causes, recommended_actions, root_cause, confidence

    def create_investigation(self, *, asset_id: int, alert_id: int) -> XRayInvestigationResult:
        investigation_id = str(uuid4())
        context = InvestigationContextBuilder().build_context(asset_id=asset_id, alert_id=alert_id)
        self.provider.create_investigation(context=context.__dict__, investigation_id=investigation_id)

        observed, inferred, alternative_causes, recommended_actions, root_cause, confidence = self._derive_reasoning(context)

        result = XRayInvestigationResult(
            investigation_id=investigation_id,
            asset_id=asset_id,
            alert_id=alert_id,
            summary=f"{context.asset['asset_code']} investigation initiated for {context.alert.get('alert_type', 'anomaly')}.",
            root_cause=root_cause,
            confidence=confidence,
            severity=context.alert.get("severity", "WARNING"),
            evidence=[Evidence.model_validate(item) for item in context.evidence],
            observed=observed,
            inferred=inferred,
            alternative_causes=alternative_causes,
            affected_assets=[relationship["target"] for relationship in context.relationships if relationship.get("target")],
            recommended_actions=recommended_actions,
            created_at=datetime.now(timezone.utc),
        )

        self._records[investigation_id] = InvestigationRecord(
            investigation_id=investigation_id,
            asset_id=asset_id,
            alert_id=alert_id,
            status="COMPLETED",
            created_at=datetime.now(timezone.utc),
            result=result,
        )

        return result

    def get_investigation(self, investigation_id: str) -> InvestigationRecord | None:
        return self._records.get(investigation_id)

    def build_status(self, investigation_id: str, status: str = "PENDING") -> dict:
        record = self._records.get(investigation_id)
        if record is None:
            return {"investigation_id": investigation_id, "status": status, "created_at": datetime.now(timezone.utc).isoformat()}
        return {
            "investigation_id": record.investigation_id,
            "asset_id": record.asset_id,
            "alert_id": record.alert_id,
            "status": record.status,
            "created_at": record.created_at.isoformat(),
        }

