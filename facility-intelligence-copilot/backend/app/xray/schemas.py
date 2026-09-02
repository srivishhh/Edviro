from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field

from app.xray.models import ResultTimestamps, IncidentAssurance


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
