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

        sensor_definitions = {
            "HVAC-001": [
                ("TEMP-001", "temperature", "°C", 18.0, 28.0),
                ("ENERGY-001", "energy", "kW", 3.0, 10.0),
                ("PRESSURE-001", "pressure", "bar", 2.0, 5.0),
                ("AIRFLOW-001", "airflow", "%", 60.0, 100.0),
            ],
            "HVAC-002": [
                ("TEMP-002", "temperature", "°C", 18.0, 28.0),
                ("ENERGY-002", "energy", "kW", 3.0, 10.0),
                ("PRESSURE-002", "pressure", "bar", 2.0, 5.0),
                ("AIRFLOW-002", "airflow", "%", 60.0, 100.0),
            ],
            "HVAC-003": [
                ("TEMP-003", "temperature", "°C", 18.0, 28.0),
                ("ENERGY-003", "energy", "kW", 3.0, 10.0),
                ("PRESSURE-003", "pressure", "bar", 2.0, 5.0),
                ("AIRFLOW-003", "airflow", "%", 60.0, 100.0),
            ],
            "HVAC-007": [
                ("TEMP-007", "temperature", "°C", 18.0, 32.0),
                ("ENERGY-007", "energy", "kW", 4.0, 15.0),
                ("PRESSURE-007", "pressure", "bar", 2.0, 6.0),
                ("AIRFLOW-007", "airflow", "%", 20.0, 100.0),
            ],
            "CHILLER-001": [
                ("TEMP-CH01", "temperature", "°C", 4.0, 12.0),
                ("ENERGY-CH01", "energy", "kW", 20.0, 60.0),
                ("PRESSURE-CH01", "pressure", "bar", 5.0, 15.0),
                ("FLOW-CH01", "airflow", "%", 80.0, 100.0),
            ],
            "CHILLER-002": [
                ("TEMP-CH02", "temperature", "°C", 4.0, 12.0),
                ("ENERGY-CH02", "energy", "kW", 20.0, 60.0),
                ("PRESSURE-CH02", "pressure", "bar", 5.0, 15.0),
                ("FLOW-CH02", "airflow", "%", 80.0, 100.0),
            ],
            "HEATPUMP-001": [
                ("TEMP-HP01", "temperature", "°C", 15.0, 35.0),
                ("ENERGY-HP01", "energy", "kW", 10.0, 30.0),
                ("PRESSURE-HP01", "pressure", "bar", 3.0, 8.0),
                ("FLOW-HP01", "airflow", "%", 60.0, 100.0),
            ],
        }

        for asset_code, sensors in sensor_definitions.items():
            target_asset = db.scalar(select(Asset).where(Asset.asset_code == asset_code))
            if target_asset is not None:
                for sensor_code, sensor_type, unit, normal_min, normal_max in sensors:
                    existing_sensor = db.scalar(select(Sensor).where(Sensor.sensor_code == sensor_code))
                    if existing_sensor is None:
                        db.add(Sensor(
                            sensor_code=sensor_code,
                            asset_id=target_asset.id,
                            sensor_type=sensor_type,
                            unit=unit,
                            normal_min=normal_min,
                            normal_max=normal_max,
                            status="online",
                            created_at=datetime.now(timezone.utc),
                        ))
        db.flush()

        hvac_001 = db.scalar(select(Asset).where(Asset.asset_code == "HVAC-001"))
        hvac_002 = db.scalar(select(Asset).where(Asset.asset_code == "HVAC-002"))
        hvac_003 = db.scalar(select(Asset).where(Asset.asset_code == "HVAC-003"))
        hvac_007 = db.scalar(select(Asset).where(Asset.asset_code == "HVAC-007"))
        chiller_001 = db.scalar(select(Asset).where(Asset.asset_code == "CHILLER-001"))
        chiller_002 = db.scalar(select(Asset).where(Asset.asset_code == "CHILLER-002"))
        heatpump_001 = db.scalar(select(Asset).where(Asset.asset_code == "HEATPUMP-001"))
        floor_2 = db.scalar(select(Floor).where(Floor.building_id == building.id, Floor.floor_number == 2))

        relationships = []
        if hvac_007 and chiller_002:
            relationships.append((hvac_007.id, "DEPENDS_ON", chiller_002.id))
        if hvac_001 and chiller_001:
            relationships.append((hvac_001.id, "DEPENDS_ON", chiller_001.id))
        if hvac_002 and chiller_001:
            relationships.append((hvac_002.id, "DEPENDS_ON", chiller_001.id))
        if hvac_003 and chiller_002:
            relationships.append((hvac_003.id, "DEPENDS_ON", chiller_002.id))
        if heatpump_001 and chiller_002:
            relationships.append((heatpump_001.id, "BACKUP_FOR", chiller_002.id))

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

