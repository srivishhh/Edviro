from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.facility import Sensor, SensorReading


class SensorRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[Sensor]:
        return self.db.query(Sensor).order_by(Sensor.id).all()

    def get_by_asset(self, asset_id: int) -> list[Sensor]:
        return self.db.query(Sensor).filter(Sensor.asset_id == asset_id).order_by(Sensor.id).all()

    def create(self, **kwargs: object) -> Sensor:
        sensor = Sensor(**kwargs)
        self.db.add(sensor)
        self.db.commit()
        self.db.refresh(sensor)
        return sensor


class TelemetryRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_reading(self, **kwargs: object) -> SensorReading:
        reading = SensorReading(**kwargs)
        self.db.add(reading)
        self.db.commit()
        self.db.refresh(reading)
        return reading

    def list_for_asset(self, asset_id: int, limit: int = 25) -> list[SensorReading]:
        return (
            self.db.query(SensorReading)
            .filter(SensorReading.asset_id == asset_id)
            .order_by(SensorReading.timestamp.desc())
            .limit(limit)
            .all()
        )
