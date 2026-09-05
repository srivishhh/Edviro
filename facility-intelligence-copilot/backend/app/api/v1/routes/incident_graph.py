from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, require_role
from app.db.session import get_db
from app.schemas.incident_graph import IncidentGraphResponse, IncidentGraphSummary
from app.services.incident_graph_service import IncidentGraphService

router = APIRouter()


@router.get(
    "/incidents/relationships",
    response_model=list[IncidentGraphSummary],
    summary="List available incident graph summaries",
    description="Returns summaries of all active and historic facility incidents available for relationship graphing. Strictly READ-ONLY.",
)
def list_incident_graphs(
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role(["VIEWER"])),
) -> list[IncidentGraphSummary]:
    try:
        service = IncidentGraphService(db_session=db)
        return service.list_available_incidents()
    except Exception:
        service = IncidentGraphService(db_session=None)
        return service.list_available_incidents()


@router.get(
    "/incidents/{incident_id}/relationships",
    response_model=IncidentGraphResponse,
    summary="Get Incident Relationship Graph",
    description="Returns the full causal dependency and relationship graph for an incident including sensors, anomalies, components, causes, impacts, and actions. Strictly READ-ONLY.",
)
def get_incident_relationship_graph(
    incident_id: str,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role(["VIEWER"])),
) -> IncidentGraphResponse:
    try:
        service = IncidentGraphService(db_session=db)
        return service.get_incident_relationship_graph(incident_id)
    except Exception:
        service = IncidentGraphService(db_session=None)
        return service.get_incident_relationship_graph(incident_id)
