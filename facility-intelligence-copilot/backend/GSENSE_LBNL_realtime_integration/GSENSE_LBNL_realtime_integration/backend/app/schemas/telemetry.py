from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    event_id: str = Field(..., min_length=1, max_length=100)
    event_type: str = Field(default="telemetry", min_length=1, max_length=50)
    asset_id: int = Field(..., gt=0)
    timestamp: datetime
    temperature: float = Field(..., ge=-100.0, le=200.0)
    pressure: float = Field(..., ge=0.0, le=300.0)
    airflow: float = Field(..., ge=0.0, le=500.0)
    energy_kw: float = Field(..., ge=0.0, le=1000.0)
    source: str | None = Field(default=None, max_length=100)
    source_timestamp: datetime | None = None
    fault_ground_truth: int | None = Field(default=None, ge=0, le=1)
    raw_metrics: dict[str, Any] | None = None

    model_config = {"from_attributes": True}
