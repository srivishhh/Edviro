from datetime import datetime

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

    model_config = {"from_attributes": True}
