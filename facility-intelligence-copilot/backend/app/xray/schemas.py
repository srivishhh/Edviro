from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class XRayCreateRequest(BaseModel):
    asset_id: int = Field(..., gt=0)
    alert_id: int = Field(..., gt=0)


class XRayInvestigationStatus(BaseModel):
    investigation_id: str
    asset_id: int
    alert_id: int
    status: str = Field(default="PENDING")
    created_at: datetime


class XRayInvestigationResponse(BaseModel):
    investigation_id: str
    asset_id: int
    alert_id: int
    summary: str
    root_cause: str
    confidence: str
    severity: str
    evidence: list[dict]
    affected_assets: list[str]
    recommended_actions: list[str]
    created_at: datetime
