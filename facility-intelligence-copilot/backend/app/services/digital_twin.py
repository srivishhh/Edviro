from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import logging

from backend.ml.features.feature_engineering import canonicalize_telemetry_dict, compute_derived_features
from backend.ml.inference.fault_predictor import FaultPredictor
from backend.counterfactual.engine import CounterfactualEngine
from backend.counterfactual.schemas import CounterfactualEvaluationResponse

logger = logging.getLogger(__name__)


@dataclass
class DigitalTwinState:
    asset_id: Any
    asset_name: str
    status: str  # "NOMINAL", "DEGRADED", "CRITICAL" / legacy "healthy", "warning", "critical"
    health_score: float  # 0.0 - 100.0
    fault_diagnosis: str
    fault_probability: float
    confidence: str
    anomalies: List[str] = field(default_factory=list)
    current_telemetry: Dict[str, float] = field(default_factory=dict)
    derived_metrics: Dict[str, float] = field(default_factory=dict)
    history_window_size: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DigitalTwinService:
    """
    GSENSE 3.0 Production Digital Twin Service.
    Maintains real thermodynamic state for AHU equipment, tracks history, evaluates ML fault models,
    and supports virtual counterfactual branch spawning.
    """
    _instance: Optional["DigitalTwinService"] = None

    def __init__(self):
        self._history_buffers: Dict[str, List[Dict[str, Any]]] = {}
        self._latest_states: Dict[str, DigitalTwinState] = {}
        self.fault_predictor = FaultPredictor.get_instance()
        self.counterfactual_engine = CounterfactualEngine.get_instance()

    @classmethod
    def get_instance(cls) -> "DigitalTwinService":
        if cls._instance is None:
            cls._instance = DigitalTwinService()
        return cls._instance

    def build_snapshot(self, asset_id: int | str, readings: list[Any]) -> DigitalTwinState:
        """Backward-compatible snapshot builder for legacy telemetry tests."""
        if not readings:
            return DigitalTwinState(
                asset_id=asset_id,
                asset_name=f"AHU-{asset_id}",
                status="healthy",
                health_score=100.0,
                fault_diagnosis="nominal",
                fault_probability=0.0,
                confidence="HIGH",
                anomalies=[],
                current_telemetry={},
                derived_metrics={},
                last_updated=datetime.now(timezone.utc).isoformat(),
            )

        temperatures = [getattr(r, "temperature", 22.0) for r in readings]
        airflows = [getattr(r, "airflow", 90.0) for r in readings]
        energy_kw_values = [getattr(r, "energy_kw", 6.0) for r in readings]

        average_temperature = sum(temperatures) / len(temperatures)
        average_airflow = sum(airflows) / len(airflows)
        peak_energy_kw = max(energy_kw_values)

        anomalies: list[str] = []
        if average_airflow < 60 or min(airflows) < 50:
            anomalies.append("airflow_restriction")
        if average_temperature > 80.0:
            anomalies.append("temperature_spike")
        if peak_energy_kw > 8.5:
            anomalies.append("energy_burst")

        if not anomalies:
            status = "healthy"
            health_score = 100.0
        elif "airflow_restriction" in anomalies and average_temperature >= 82.0:
            status = "critical"
            health_score = 55.0
        else:
            status = "warning"
            health_score = 72.0

        return DigitalTwinState(
            asset_id=asset_id,
            asset_name=f"AHU-{asset_id}",
            status=status,
            health_score=health_score,
            fault_diagnosis="fan_belt_slip" if "airflow_restriction" in anomalies else "nominal",
            fault_probability=0.85 if anomalies else 0.0,
            confidence="HIGH",
            anomalies=anomalies,
            current_telemetry={
                "zone_temp": average_temperature,
                "sa_cfm": average_airflow * 25.0,
                "power": peak_energy_kw,
            },
            derived_metrics={},
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

    def process_telemetry_frame(self, asset_id: str, raw_reading: Dict[str, Any], asset_name: str = "AHU-007 Main Rooftop") -> DigitalTwinState:
        """
        Ingests a live or replayed telemetry frame, executes ML fault classification,
        and computes operational health metrics.
        """
        canonical = canonicalize_telemetry_dict(raw_reading)
        derived = compute_derived_features(canonical)

        # Buffer history (keep rolling 60 points)
        if asset_id not in self._history_buffers:
            self._history_buffers[asset_id] = []
        self._history_buffers[asset_id].append({**canonical, **derived, "timestamp": datetime.now(timezone.utc).isoformat()})
        if len(self._history_buffers[asset_id]) > 60:
            self._history_buffers[asset_id].pop(0)

        # Execute ML Fault Predictor
        ml_res = self.fault_predictor.predict(canonical)
        fault_class = ml_res["fault_class"]
        fault_prob = ml_res["fault_probability"]
        confidence = ml_res["confidence"]
        anomalies = ml_res["indicators"]

        # Dynamic Health Score Calculation
        # Base 100 minus fault severity penalty + comfort penalty + duct pressure penalty
        health = 100.0
        if fault_class != "nominal":
            health -= fault_prob * 35.0

        zone_t = canonical.get("zone_temp", 22.8)
        if zone_t > 25.5:
            health -= min(25.0, (zone_t - 25.5) * 8.0)
        elif zone_t < 20.0:
            health -= min(20.0, (20.0 - zone_t) * 6.0)

        sp = canonical.get("sa_sp", 1.5)
        if sp > 3.5:
            health -= min(30.0, (sp - 3.5) * 20.0)

        health = max(10.0, min(100.0, round(health, 1)))

        # Operational Status
        if health >= 80.0 and fault_class == "nominal":
            status = "NOMINAL"
        elif health >= 55.0:
            status = "DEGRADED"
        else:
            status = "CRITICAL"

        twin_state = DigitalTwinState(
            asset_id=asset_id,
            asset_name=asset_name,
            status=status,
            health_score=health,
            fault_diagnosis=fault_class,
            fault_probability=fault_prob,
            confidence=confidence,
            anomalies=anomalies,
            current_telemetry=canonical,
            derived_metrics=derived,
            history_window_size=len(self._history_buffers[asset_id]),
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

        self._latest_states[asset_id] = twin_state
        return twin_state

    def get_state(self, asset_id: str = "AHU-007") -> Optional[DigitalTwinState]:
        return self._latest_states.get(asset_id)

    def get_history(self, asset_id: str = "AHU-007") -> List[Dict[str, Any]]:
        return self._history_buffers.get(asset_id, [])

    def evaluate_counterfactual(
        self,
        asset_id: str = "AHU-007",
        incident_id: Optional[str] = None,
        sns_proposed_plan: Optional[Dict[str, Any]] = None,
    ) -> CounterfactualEvaluationResponse:
        """
        Runs counterfactual simulation across candidate interventions starting from current physical twin state.
        """
        cur_state = self.get_state(asset_id)
        if not cur_state:
            # Generate nominal baseline if no frame has arrived yet
            raw = {
                "oa_temp": 24.0, "ra_temp": 23.0, "ma_temp": 23.5, "sa_temp": 14.5,
                "zone_temp": 22.8, "oa_dmpr": 25.0, "chwc_vlv": 35.0, "sf_spd": 70.0,
                "sa_cfm": 2500.0, "sa_sp": 1.5, "power": 8.5
            }
            cur_state = self.process_telemetry_frame(asset_id, raw)

        return self.counterfactual_engine.evaluate_facility_state(
            asset_id=asset_id,
            current_telemetry=cur_state.current_telemetry,
            fault_diagnosis=cur_state.fault_diagnosis,
            incident_id=incident_id,
            sns_proposed_plan=sns_proposed_plan,
        )
