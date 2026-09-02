from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class SNSRelatedSensorData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    airflow: float = Field(default=42.0, ge=0.0, le=500.0)
    expected_airflow: float = Field(default=70.0, ge=0.0, le=500.0)
    fan_status: str = Field(default="normal", max_length=64)
    energy_kw: float = Field(default=12.4, ge=0.0, le=5000.0)
    expected_energy_kw: float = Field(default=8.1, ge=0.0, le=5000.0)


class SNSDigitalTwinData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    facility: str = Field(default="School Building A", max_length=128)
    building: str = Field(default="Building A", max_length=128)
    floor: str = Field(default="Floor 2", max_length=128)
    asset: str = Field(default="HVAC-007", max_length=128)
    asset_type: str = Field(default="AHU", max_length=64)
    relationships: list[str] = Field(
        default_factory=lambda: [
            "HVAC-007 -> TEMP-007",
            "HVAC-007 -> AIRFLOW-007",
            "HVAC-007 -> FAN-007",
        ],
        max_length=100,
    )


class SNSEventPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    investigation_id: str = Field(default="INV-001", min_length=1, max_length=128)
    facility_id: str = Field(default="FAC-001", min_length=1, max_length=64)
    facility_name: str = Field(default="School Building A", max_length=128)
    facility_type: str = Field(default="school", max_length=64)
    building_id: str = Field(default="BLDG-001", max_length=64)
    floor_id: str = Field(default="FLOOR-02", max_length=64)
    asset_id: str = Field(default="HVAC-007", min_length=1, max_length=64)
    asset_name: str = Field(default="AHU Floor 2", max_length=128)
    sensor_id: str = Field(default="TEMP-007", min_length=1, max_length=64)
    metric: str = Field(default="temperature", min_length=1, max_length=64)
    current_value: float = Field(default=31.8, ge=-100.0, le=5000.0)
    unit: str = Field(default="C", max_length=32)
    expected_min: float = Field(default=20.0, ge=-100.0, le=5000.0)
    expected_max: float = Field(default=26.0, ge=-100.0, le=5000.0)
    timestamp: str = Field(default="2026-09-02T11:00:00", max_length=64)
    historical_telemetry: list[float] = Field(
        default_factory=lambda: [23.2, 23.8, 24.1, 24.5, 25.0],
        max_length=500,
    )
    related_sensor_data: SNSRelatedSensorData = Field(default_factory=SNSRelatedSensorData)
    digital_twin: SNSDigitalTwinData = Field(default_factory=SNSDigitalTwinData)


class SNSGenericEventRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    investigation_id: str | None = Field(default=None, max_length=128)
    facility_id: str | None = Field(default=None, max_length=64)
    facility_name: str | None = Field(default=None, max_length=128)
    facility_type: str | None = Field(default=None, max_length=64)
    building_id: str | None = Field(default=None, max_length=64)
    floor_id: str | None = Field(default=None, max_length=64)
    asset_id: str | None = Field(default=None, max_length=64)
    asset_name: str | None = Field(default=None, max_length=128)
    sensor_id: str | None = Field(default=None, max_length=64)
    metric: str | None = Field(default=None, max_length=64)
    current_value: float | None = Field(default=None, ge=-100.0, le=5000.0)
    unit: str | None = Field(default=None, max_length=32)
    expected_min: float | None = Field(default=None, ge=-100.0, le=5000.0)
    expected_max: float | None = Field(default=None, ge=-100.0, le=5000.0)
    timestamp: str | None = Field(default=None, max_length=64)
    historical_telemetry: list[float] | None = Field(default=None, max_length=500)
    related_sensor_data: dict[str, Any] | None = None
    digital_twin: dict[str, Any] | None = None
