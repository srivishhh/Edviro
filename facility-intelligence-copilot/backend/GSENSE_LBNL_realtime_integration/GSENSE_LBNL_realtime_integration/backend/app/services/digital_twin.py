from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.schemas.telemetry import TelemetryEvent


@dataclass
class DigitalTwinState:
    asset_id: int
    status: str
    health_score: float
    anomalies: list[str] = field(default_factory=list)
    average_temperature: float | None = None
    average_airflow: float | None = None
    last_updated: datetime | None = None


class DigitalTwinService:
    def build_snapshot(self, asset_id: int, readings: list[TelemetryEvent]) -> DigitalTwinState:
        if not readings:
            return DigitalTwinState(
                asset_id=asset_id,
                status="healthy",
                health_score=100.0,
                anomalies=[],
                average_temperature=0.0,
                average_airflow=0.0,
                last_updated=datetime.now(timezone.utc),
            )

        temperatures = [reading.temperature for reading in readings]
        airflows = [reading.airflow for reading in readings]
        energy_kw_values = [reading.energy_kw for reading in readings]

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
            status=status,
            health_score=health_score,
            anomalies=anomalies,
            average_temperature=average_temperature,
            average_airflow=average_airflow,
            last_updated=datetime.now(timezone.utc),
        )
