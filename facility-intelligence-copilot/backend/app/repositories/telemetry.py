from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.facility import Sensor, SensorReading


class TelemetryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_reading(self, *, sensor_id: int, timestamp: datetime, value: float) -> SensorReading:
        reading = SensorReading(sensor_id=sensor_id, timestamp=timestamp, value=value)
        self.db.add(reading)
        self.db.commit()
        self.db.refresh(reading)
        return reading

    def create_readings(self, readings: list[dict]) -> list[SensorReading]:
        rows: list[SensorReading] = []
        for reading in readings:
            row = SensorReading(**reading)
            self.db.add(row)
            rows.append(row)
        self.db.commit()
        for row in rows:
            self.db.refresh(row)
        return rows

    def get_latest_readings(self, sensor_ids: list[int] | None = None, limit: int = 20) -> list[SensorReading]:
        query = self.db.query(SensorReading)
        if sensor_ids:
            query = query.filter(SensorReading.sensor_id.in_(sensor_ids))
        return query.order_by(desc(SensorReading.timestamp)).limit(limit).all()

    def get_readings_for_asset(self, asset_id: int, limit: int = 25) -> list[SensorReading]:
        sensor_ids = [sensor.id for sensor in self.db.query(Sensor).filter(Sensor.asset_id == asset_id).all()]
        if not sensor_ids:
            return []
        return (
            self.db.query(SensorReading)
            .filter(SensorReading.sensor_id.in_(sensor_ids))
            .order_by(desc(SensorReading.timestamp))
            .limit(limit)
            .all()
        )
