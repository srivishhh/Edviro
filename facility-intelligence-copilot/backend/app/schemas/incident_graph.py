from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    ASSET = "ASSET"
    COMPONENT = "COMPONENT"
    SENSOR = "SENSOR"
    ANOMALY = "ANOMALY"
    INCIDENT = "INCIDENT"
    ROOT_CAUSE = "ROOT_CAUSE"
    IMPACT = "IMPACT"
    ACTION = "ACTION"


class ConfidenceLevel(str, Enum):
    CONFIRMED = "CONFIRMED"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    SUSPECTED = "SUSPECTED"
    OBSERVED = "OBSERVED"


class NodeTelemetry(BaseModel):
    metric: str
    current_value: float | int | str
    expected_range: str
    unit: str = ""
    baseline: float | int | str | None = None
    status: str = "NORMAL"  # NORMAL, WARNING, CRITICAL


class IncidentGraphNode(BaseModel):
    id: str
    type: NodeType
    label: str
    category: str = "Observation"  # Observation, Anomaly, Component, Causal Hypothesis, Operational Impact, Action
    status: str = "HEALTHY"  # HEALTHY, WARNING, CRITICAL, NEUTRAL
    confidence: str | None = None  # e.g. "88%", "Observed", "Suspected"
    confidence_level: ConfidenceLevel = ConfidenceLevel.OBSERVED
    telemetry: NodeTelemetry | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class IncidentGraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship: str  # measures, reports_anomaly, associated_with, depends_on, affects, caused_by, produces, requires
    confidence: str | None = None  # e.g. "Confirmed", "88% Primary", "34% Secondary"
    label: str | None = None


class SimilarHistoricalIncident(BaseModel):
    memory_id: str  # e.g. "MEM-2026-104"
    incident_number: str  # e.g. "#104"
    incident_type: str
    asset_code: str
    similarity_pct: int  # e.g. 94
    root_cause: str
    corrective_action: str
    timestamp: str


class IncidentGraphSummary(BaseModel):
    incident_id: str | int
    incident_name: str
    alert_type: str
    asset_id: int
    asset_name: str
    asset_code: str
    severity: str  # CRITICAL, WARNING, INFO
    confidence: str  # e.g. "87%"
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH
    affected_components_count: int
    possible_causes_count: int
    energy_impact: str  # e.g. "Elevated (+4.2 kW)"
    status: str = "OPEN"
    detected_at: str | None = None


class IncidentGraphResponse(BaseModel):
    summary: IncidentGraphSummary
    nodes: list[IncidentGraphNode]
    edges: list[IncidentGraphEdge]
    historical_matches: list[SimilarHistoricalIncident] = Field(default_factory=list)
