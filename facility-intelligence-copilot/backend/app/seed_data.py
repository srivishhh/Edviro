from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.facility import Alert, Asset, AssetRelationship, Building, Floor, Sensor


def seed_demo_data() -> None:
    db: Session = SessionLocal()
    try:
        building = db.scalar(select(Building).where(Building.code == "BLDG-A"))
        if building is None:
            building = Building(name="Building A", code="BLDG-A")
            db.add(building)
            db.flush()

        floors = [
            Floor(building_id=building.id, name="Floor 1", floor_number=1),
            Floor(building_id=building.id, name="Floor 2", floor_number=2),
            Floor(building_id=building.id, name="Floor 3", floor_number=3),
        ]
        for floor in floors:
            existing = db.scalar(select(Floor).where(Floor.building_id == building.id, Floor.floor_number == floor.floor_number))
            if existing is None:
                db.add(floor)
        db.flush()

        asset_specs = [
            ("HVAC-001", "HVAC", "HVAC-001", 1),
            ("HVAC-002", "HVAC", "HVAC-002", 1),
            ("HVAC-003", "HVAC", "HVAC-003", 2),
            ("HVAC-007", "HVAC", "HVAC-007", 2),
            ("CHILLER-001", "CHILLER", "CHILLER-001", 3),
            ("CHILLER-002", "CHILLER", "CHILLER-002", 2),
            ("HEATPUMP-001", "HEAT_PUMP", "HEATPUMP-001", 2),
        ]

        for asset_code, asset_type, name, floor_number in asset_specs:
            floor = db.scalar(select(Floor).where(Floor.building_id == building.id, Floor.floor_number == floor_number))
            asset = db.scalar(select(Asset).where(Asset.asset_code == asset_code))
            if asset is None:
                db.add(Asset(asset_code=asset_code, name=name, asset_type=asset_type, building_id=building.id, floor_id=floor.id if floor else None, status="healthy", health_score=92.0, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)))
        db.flush()

        hvac_007 = db.scalar(select(Asset).where(Asset.asset_code == "HVAC-007"))
        if hvac_007 is not None:
            sensors = [
                ("TEMP-007", "temperature", "°C", 18.0, 32.0),
                ("ENERGY-007", "energy", "kW", 4.0, 15.0),
                ("PRESSURE-007", "pressure", "bar", 2.0, 6.0),
                ("AIRFLOW-007", "airflow", "%", 20.0, 100.0),
            ]
            for sensor_code, sensor_type, unit, normal_min, normal_max in sensors:
                existing_sensor = db.scalar(select(Sensor).where(Sensor.sensor_code == sensor_code))
                if existing_sensor is None:
                    db.add(Sensor(sensor_code=sensor_code, asset_id=hvac_007.id, sensor_type=sensor_type, unit=unit, normal_min=normal_min, normal_max=normal_max, status="online", created_at=datetime.now(timezone.utc)))
        db.flush()

        hvac_007 = db.scalar(select(Asset).where(Asset.asset_code == "HVAC-007"))
        if hvac_007 is not None:
            relationships = [
                (hvac_007.id, "SERVES", db.scalar(select(Floor).where(Floor.building_id == building.id, Floor.floor_number == 2)).id),
                (hvac_007.id, "DEPENDS_ON", db.scalar(select(Asset).where(Asset.asset_code == "CHILLER-002")).id),
            ]
            for source_asset_id, relationship_type, target_asset_id in relationships:
                existing = db.scalar(
                    select(AssetRelationship).where(
                        AssetRelationship.source_asset_id == source_asset_id,
                        AssetRelationship.relationship_type == relationship_type,
                        AssetRelationship.target_asset_id == target_asset_id,
                    )
                )
                if existing is None:
                    db.add(AssetRelationship(source_asset_id=source_asset_id, relationship_type=relationship_type, target_asset_id=target_asset_id))

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
    print("Seed data loaded")
