from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class IncidentAssurance(BaseModel):
    decision: str
    confidence: float
    notification_allowed: bool


class ResultTimestamps(BaseModel):
    received_at: str | None = None
    completed_at: str | None = None


class XRayInvestigationRequest(BaseModel):
    asset_id: int = Field(..., gt=0)
    alert_id: int = Field(..., gt=0)
    investigation_id: str | None = None
    requested_at: datetime | None = None


class XRayInvestigationResult(BaseModel):
    investigation_id: str
    event_id: str
    status: str
    event_class: str

    condition_intelligence: Dict[str, Any] = Field(default_factory=dict)
    asset_context: Dict[str, Any] = Field(default_factory=dict)
    operational_risk: Dict[str, Any] = Field(default_factory=dict)

    diagnostic_reasoning: Dict[str, Any] = Field(default_factory=dict)
    active_fault_isolation: Dict[str, Any] = Field(default_factory=dict)

    incident_assurance: IncidentAssurance

    maintenance_optimization: Dict[str, Any] = Field(default_factory=dict)
    energy_cost_optimization: Dict[str, Any] = Field(default_factory=dict)
    prescriptive_operations: Dict[str, Any] = Field(default_factory=dict)
    communication: Dict[str, Any] = Field(default_factory=dict)

    timestamps: ResultTimestamps = Field(default_factory=ResultTimestamps)

    model_config = {"from_attributes": True}


class Evidence(BaseModel):
    source: str = Field(..., min_length=1)
    metric: str = Field(..., min_length=1)
    value: float | int | str = Field(...)
    expected_range: str = Field(default="n/a")
    timestamp: datetime | str | None = None
    interpretation: str = Field(default="")
