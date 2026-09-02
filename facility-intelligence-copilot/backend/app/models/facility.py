from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    code = Column(String(50), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    floors = relationship("Floor", back_populates="building")
    assets = relationship("Asset", back_populates="building")


class Floor(Base):
    __tablename__ = "floors"

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    floor_number = Column(Integer, nullable=False)

    building = relationship("Building", back_populates="floors")
    assets = relationship("Asset", back_populates="floor")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    asset_type = Column(String(50), nullable=False)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=True, index=True)
    floor_id = Column(Integer, ForeignKey("floors.id"), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="healthy")
    health_score = Column(Float, nullable=False, default=100.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    building = relationship("Building", back_populates="assets")
    floor = relationship("Floor", back_populates="assets")
    sensors = relationship("Sensor", back_populates="asset")
    alerts = relationship("Alert", back_populates="asset")
    source_relationships = relationship("AssetRelationship", foreign_keys="AssetRelationship.source_asset_id", back_populates="source_asset")
    target_relationships = relationship("AssetRelationship", foreign_keys="AssetRelationship.target_asset_id", back_populates="target_asset")


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True)
    sensor_code = Column(String(80), unique=True, nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    sensor_type = Column(String(80), nullable=False)
    unit = Column(String(30), nullable=True)
    normal_min = Column(Float, nullable=True)
    normal_max = Column(Float, nullable=True)
    status = Column(String(30), nullable=False, default="online")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    asset = relationship("Asset", back_populates="sensors")
    readings = relationship("SensorReading", back_populates="sensor")


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    __table_args__ = (Index("ix_sensor_readings_sensor_timestamp", "sensor_id", "timestamp"),)

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=False)

    sensor = relationship("Sensor", back_populates="readings")


class AssetRelationship(Base):
    __tablename__ = "asset_relationships"

    id = Column(Integer, primary_key=True, index=True)
    source_asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    relationship_type = Column(String(60), nullable=False)
    target_asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)

    source_asset = relationship("Asset", foreign_keys=[source_asset_id], back_populates="source_relationships")
    target_asset = relationship("Asset", foreign_keys=[target_asset_id], back_populates="target_relationships")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    alert_type = Column(String(80), nullable=False, index=True)
    severity = Column(String(30), nullable=False, default="WARNING")
    message = Column(Text, nullable=False)
    anomaly_score = Column(Float, nullable=False, default=0.0)
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="OPEN")

    asset = relationship("Asset", back_populates="alerts")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    incident_type = Column(String(80), nullable=False)
    severity = Column(String(30), nullable=False)
    summary = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="open")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    work_order = Column(String(80), nullable=False, unique=True)
    maintenance_type = Column(String(80), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="scheduled")
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(30), nullable=False, default="medium")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WhatIfScenario(Base):
    __tablename__ = "what_if_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="draft")
    is_active = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
