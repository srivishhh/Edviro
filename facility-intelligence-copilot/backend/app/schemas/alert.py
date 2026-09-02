from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class AlertCreate(BaseModel):
    asset_id: int = Field(..., gt=0)
    alert_type: str = Field(..., min_length=1, max_length=80)
    severity: str = Field(default="WARNING", min_length=1, max_length=30)
    message: str = Field(..., min_length=1)
    anomaly_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: AlertStatus = AlertStatus.OPEN


class AlertUpdate(BaseModel):
    status: AlertStatus



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
