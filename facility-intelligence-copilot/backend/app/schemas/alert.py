from datetime import datetime

from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    asset_id: int = Field(..., gt=0)
    alert_type: str = Field(..., min_length=1, max_length=80)
    severity: str = Field(default="WARNING", min_length=1, max_length=30)
    message: str = Field(..., min_length=1)
    anomaly_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: str = Field(default="OPEN", min_length=1, max_length=30)


class AlertUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=30)


class AlertRead(BaseModel):
    id: int
    asset_id: int
    alert_type: str
    severity: str
    message: str
    anomaly_score: float
    detected_at: datetime
    status: str

    model_config = {"from_attributes": True}
