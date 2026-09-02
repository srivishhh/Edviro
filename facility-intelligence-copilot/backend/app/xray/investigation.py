from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.models.facility import Alert, Asset
from app.repositories.alerts import AlertRepository
from app.repositories.telemetry import TelemetryRepository
from app.xray.evidence import build_evidence_items


@dataclass
class InvestigationContext:
    asset: dict
    current_state: dict
    recent_history: list[dict]
    alert: dict
    relationships: list[dict]
    anomaly: dict
    evidence: list[dict] = field(default_factory=list)


class InvestigationContextBuilder:
    def build_context(self, asset_id: int, alert_id: int, db=None) -> InvestigationContext:
        asset = self._resolve_asset(asset_id, db)
        alert = self._resolve_alert(alert_id, db)
        current_state = self._resolve_current_state(asset_id, db)
        recent_history = self._resolve_recent_history(asset_id, db)
        relationships = self._resolve_relationships(asset_id)
        anomaly = self._resolve_anomaly(alert)
        evidence = build_evidence_items(current_state, recent_history, alert, relationships)

        return InvestigationContext(
            asset=asset,
            current_state=current_state,
            recent_history=recent_history,
            alert=alert,
            relationships=relationships,
            anomaly=anomaly,
            evidence=[item.model_dump(mode="json") for item in evidence],
        )

    def _resolve_asset(self, asset_id: int, db=None) -> dict:
        if db is not None:
            record = db.query(Asset).filter(Asset.id == asset_id).first()
            if record is not None:
                return {
                    "id": record.id,
                    "asset_code": record.asset_code,
                    "name": record.name,
                    "asset_type": record.asset_type,
                    "status": record.status,
                    "health_score": record.health_score,
                    "building_id": record.building_id,
                    "floor_id": record.floor_id,
                }

        return {
            "id": asset_id,
            "asset_code": "HVAC-007",
            "name": "HVAC-007",
            "asset_type": "HVAC",
            "status": "warning",
            "health_score": 68,
            "building_id": 1,
            "floor_id": 2,
        }

    def _resolve_alert(self, alert_id: int, db=None) -> dict:
        if db is not None:
            record = db.query(Alert).filter(Alert.id == alert_id).first()
            if record is not None:
                return {
                    "id": record.id,
                    "asset_id": record.asset_id,
                    "alert_type": record.alert_type,
                    "severity": record.severity,
                    "message": record.message,
                    "anomaly_score": record.anomaly_score,
                    "status": record.status,
                    "detected_at": record.detected_at.isoformat() if record.detected_at else None,
                }

        alerts_map = {
            101: {
                "id": 101,
                "asset_id": 7,
                "alert_type": "AIRFLOW_RESTRICTION",
                "severity": "WARNING",
                "message": "Airflow below baseline with elevated temperature and energy use.",
                "anomaly_score": 0.82,
                "status": "OPEN",
                "detected_at": "2026-09-01T12:15:00Z",
            },
            102: {
                "id": 102,
                "asset_id": 7,
                "alert_type": "HIGH_ENERGY",
                "severity": "WARNING",
                "message": "Energy consumption above expected operating range.",
                "anomaly_score": 0.68,
                "status": "OPEN",
                "detected_at": "2026-09-01T12:15:00Z",
            },
            103: {
                "id": 103,
                "asset_id": 7,
                "alert_type": "HIGH_TEMPERATURE",
                "severity": "WARNING",
                "message": "Temperature exceeds safe operating baseline.",
                "anomaly_score": 0.71,
                "status": "OPEN",
                "detected_at": "2026-09-01T12:15:00Z",
            },
            104: {
                "id": 104,
                "asset_id": 7,
                "alert_type": "PRESSURE_ANOMALY",
                "severity": "WARNING",
                "message": "Pressure is above expected range for the asset.",
                "anomaly_score": 0.63,
                "status": "OPEN",
                "detected_at": "2026-09-01T12:15:00Z",
            },
            105: {
                "id": 105,
                "asset_id": 7,
                "alert_type": "SENSOR_FAILURE",
                "severity": "CRITICAL",
                "message": "Telemetry sensor values indicate a likely fault state.",
                "anomaly_score": 0.95,
                "status": "OPEN",
                "detected_at": "2026-09-01T12:15:00Z",
            },
        }

        return alerts_map.get(alert_id, alerts_map[101])

    def _resolve_current_state(self, asset_id: int, db=None) -> dict:
        if asset_id == 7:
            return {
                "timestamp": "2026-09-01T12:15:00Z",
                "temperature": 30.1,
                "energy_kw": 12.3,
                "pressure": 4.3,
                "airflow": 64.0,
            }
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": 23.0,
            "energy_kw": 5.5,
            "pressure": 3.8,
            "airflow": 95.0,
        }

    def _resolve_recent_history(self, asset_id: int, db=None) -> list[dict]:
        if asset_id == 7:
            return [
                {"timestamp": "2026-09-01T12:00:00Z", "temperature": 28.9, "energy_kw": 10.8, "pressure": 4.5, "airflow": 72.0},
                {"timestamp": "2026-09-01T12:05:00Z", "temperature": 29.4, "energy_kw": 11.2, "pressure": 4.6, "airflow": 70.0},
                {"timestamp": "2026-09-01T12:10:00Z", "temperature": 29.7, "energy_kw": 11.8, "pressure": 4.5, "airflow": 68.0},
                {"timestamp": "2026-09-01T12:15:00Z", "temperature": 30.1, "energy_kw": 12.3, "pressure": 4.3, "airflow": 64.0},
            ]
        return [
            {"timestamp": "2026-09-01T09:00:00Z", "temperature": 22.4, "energy_kw": 5.2, "pressure": 3.6, "airflow": 98.0},
            {"timestamp": "2026-09-01T09:05:00Z", "temperature": 23.1, "energy_kw": 5.5, "pressure": 3.8, "airflow": 96.0},
        ]

    def _resolve_relationships(self, asset_id: int) -> list[dict]:
        if asset_id == 7:
            return [
                {"type": "SERVES", "target": "Floor 2"},
                {"type": "DEPENDS ON", "target": "CHILLER-002"},
                {"type": "MONITORED BY", "target": "TEMP-007"},
                {"type": "MONITORED BY", "target": "ENERGY-007"},
                {"type": "MONITORED BY", "target": "PRESSURE-007"},
                {"type": "MONITORED BY", "target": "AIRFLOW-007"},
            ]
        return [{"type": "SERVES", "target": "Floor 1"}]

    def _resolve_anomaly(self, alert: dict) -> dict:
        alert_type = alert.get("alert_type", "AIRFLOW_RESTRICTION")
        score = float(alert.get("anomaly_score", 0.8))
        severity = alert.get("severity", "WARNING")

        descriptions = {
            "AIRFLOW_RESTRICTION": "Airflow is below expected baseline range while temperature and energy consumption rise.",
            "HIGH_ENERGY": "Electrical power demand is significantly above normal steady-state operation.",
            "HIGH_TEMPERATURE": "Supply temperature has exceeded operating threshold, indicating thermal exchange degradation.",
            "PRESSURE_ANOMALY": "Static differential pressure exceeds nominal operating envelope.",
            "SENSOR_FAILURE": "Telemetry signal is outside physical operating envelope indicating sensor loss or electrical fault.",
        }

        return {
            "type": alert_type,
            "severity": severity,
            "score": score,
            "description": descriptions.get(alert_type, "Operational deviation detected against baseline model."),
        }

