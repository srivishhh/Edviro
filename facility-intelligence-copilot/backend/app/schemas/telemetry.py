from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class TelemetryEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    event_id: str = Field(..., min_length=1, max_length=128)
    event_type: str = Field(default="telemetry", min_length=1, max_length=50)
    asset_id: int = Field(..., gt=0)
    timestamp: datetime
    temperature: float = Field(..., ge=-100.0, le=200.0)
    pressure: float = Field(..., ge=0.0, le=500.0)
    airflow: float = Field(..., ge=0.0, le=50000.0)
    energy_kw: float = Field(..., ge=0.0, le=5000.0)
    raw_data: dict[str, Any] | None = None
