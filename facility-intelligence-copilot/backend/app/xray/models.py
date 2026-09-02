from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    source: str = Field(..., min_length=1)
    metric: str = Field(..., min_length=1)
    value: float | int | str = Field(...)
    current_value: float | int | str | None = None
    baseline: float | int | str | None = None
    expected_range: str = Field(default="n/a")
    timestamp: datetime | str | None = None
    interpretation: str = Field(default="")
    importance: float = Field(default=1.0)


class XRayInvestigationRequest(BaseModel):
    asset_id: int = Field(..., gt=0)
    alert_id: int = Field(..., gt=0)
    investigation_id: str | None = None
    requested_at: datetime | None = None


class XRayInvestigationResult(BaseModel):
    investigation_id: str
    asset_id: int
    alert_id: int
    summary: str
    root_cause: str
    confidence: str
    severity: str
    evidence: list[Evidence]
    observed: list[str] = Field(default_factory=list)
    inferred: list[str] = Field(default_factory=list)
    alternative_causes: list[str] = Field(default_factory=list)
    affected_assets: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}

