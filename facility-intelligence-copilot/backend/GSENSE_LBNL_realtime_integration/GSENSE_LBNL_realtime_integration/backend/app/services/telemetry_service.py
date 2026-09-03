from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.facility import Alert, Asset, Sensor, SensorReading
from app.repositories.alerts import AlertRepository
from app.repositories.telemetry import TelemetryRepository
from app.schemas.telemetry import TelemetryEvent
from app.services.digital_twin import DigitalTwinService


class TelemetryService:
    def __init__(self, db: Session | None = None):
        self.db = db or SessionLocal()

    def _sensor_value(self, sensor: Sensor, event: TelemetryEvent) -> float | None:
        sensor_key = (sensor.sensor_type or "").strip().lower()
        if sensor_key in {"temperature", "temp", "temp_sensor", "temperatures"}:
            return event.temperature
        if sensor_key in {"energy", "energy_kw", "power"}:
            return event.energy_kw
        if sensor_key in {"pressure", "psi", "bar"}:
            return event.pressure
        if sensor_key in {"airflow", "airflow_pct", "airflow_percent"}:
            return event.airflow
        if sensor_key.startswith("temp"):
            return event.temperature
        if sensor_key.startswith("energy"):
            return event.energy_kw
        if sensor_key.startswith("pressure"):
            return event.pressure
        if sensor_key.startswith("airflow"):
            return event.airflow
        return None

    @staticmethod
    def _detect_anomalies(event: TelemetryEvent) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []

        if event.airflow < 85 and event.temperature >= 27 and event.energy_kw >= 9:
            alerts.append({
                "alert_type": "AIRFLOW_RESTRICTION",
                "severity": "WARNING",
                "message": "Airflow below baseline with elevated temperature and energy use.",
                "anomaly_score": 0.82,
            })

        if event.energy_kw > 10:
            alerts.append({
                "alert_type": "HIGH_ENERGY",
                "severity": "WARNING",
                "message": "Energy consumption above expected operating range.",
                "anomaly_score": 0.68,
            })

        if event.temperature > 28:
            alerts.append({
                "alert_type": "HIGH_TEMPERATURE",
                "severity": "WARNING",
                "message": "Temperature exceeds safe operating baseline.",
                "anomaly_score": 0.71,
            })

        if event.pressure > 4.2:
            alerts.append({
                "alert_type": "PRESSURE_ANOMALY",
                "severity": "WARNING",
                "message": "Pressure is above expected range for the asset.",
                "anomaly_score": 0.63,
            })

        if event.airflow <= 0 or event.temperature <= -20:
            alerts.append({
                "alert_type": "SENSOR_FAILURE",
                "severity": "CRITICAL",
                "message": "Telemetry sensor values indicate a likely fault state.",
                "anomaly_score": 0.95,
            })

        # LBNL RTU replay: pressure and electrical demand rise during condenser-fouling
        # periods. Ground truth is retained for evaluation only; it is NOT used to create alerts.
        if event.source == "LBNL_RTU" and event.pressure >= 25.0 and event.energy_kw >= 8.0:
            alerts.append({
                "alert_type": "CONDENSER_FOULING",
                "severity": "WARNING",
                "message": "RTU discharge pressure and electrical demand are elevated; condenser performance may be degraded.",
                "anomaly_score": 0.88,
            })

        return alerts

    def _update_asset_state(self, asset: Asset, event: TelemetryEvent) -> dict[str, Any]:
        latest = [event]
        state = DigitalTwinService().build_snapshot(asset.id, latest)
        asset.status = state.status
        asset.health_score = max(0.0, state.health_score)
        asset.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return {
            "asset_id": asset.id,
            "status": asset.status,
            "health_score": asset.health_score,
            "anomalies": state.anomalies,
            "last_updated": state.last_updated,
        }

    def process_event(self, event: TelemetryEvent) -> dict[str, Any]:
        asset = self.db.query(Asset).filter(Asset.id == event.asset_id).first()
        if asset is None:
            raise ValueError(f"Asset {event.asset_id} not found")

        sensors = self.db.query(Sensor).filter(Sensor.asset_id == asset.id).all()
        telemetry_repo = TelemetryRepository(self.db)
        alert_repo = AlertRepository(self.db)

        for sensor in sensors:
            value = self._sensor_value(sensor, event)
            if value is None:
                continue
            telemetry_repo.create_reading(sensor_id=sensor.id, timestamp=event.timestamp, value=value)

        twin_state = self._update_asset_state(asset, event)
        alerts: list[dict[str, Any]] = []
        for anomaly in self._detect_anomalies(event):
            alert = alert_repo.upsert_open_alert(
                asset_id=asset.id,
                alert_type=anomaly["alert_type"],
                severity=anomaly["severity"],
                message=anomaly["message"],
                anomaly_score=float(anomaly["anomaly_score"]),
            )
            alerts.append({
                "id": alert.id,
                "asset_id": alert.asset_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "status": alert.status,
                "message": alert.message,
                "anomaly_score": alert.anomaly_score,
                "detected_at": alert.detected_at.isoformat(),
            })

        return {
            "asset_id": asset.id,
            "status": twin_state["status"],
            "health_score": twin_state["health_score"],
            "anomalies": twin_state["anomalies"],
            "alerts": alerts,
            "last_updated": twin_state["last_updated"].isoformat() if twin_state["last_updated"] else None,
        }

    def list_alerts(self, asset_id: int | None = None) -> list[Alert]:
        alert_repo = AlertRepository(self.db)
        if asset_id is not None:
            return alert_repo.list_for_asset(asset_id)
        return alert_repo.list()
