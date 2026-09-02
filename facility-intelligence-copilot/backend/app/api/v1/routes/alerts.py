from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, require_role
from app.db.session import get_db
from app.models.facility import Alert
from app.repositories.alerts import AlertRepository
from app.schemas.alert import AlertRead, AlertStatus, AlertUpdate

router = APIRouter()

FALLBACK_ALERTS = [
    {
        "id": 101,
        "asset_id": 7,
        "alert_type": "AIRFLOW_RESTRICTION",
        "severity": "WARNING",
        "message": "Airflow is below expected range while temperature and energy consumption rise.",
        "anomaly_score": 0.82,
        "status": "OPEN",
        "detected_at": "2026-09-01T12:15:00Z",
        "created_at": "2026-09-01T12:15:00Z",
    },
    {
        "id": 102,
        "asset_id": 1,
        "alert_type": "HIGH_ENERGY",
        "severity": "INFO",
        "message": "Energy consumption slightly elevated during peak cooling duty.",
        "anomaly_score": 0.54,
        "status": "OPEN",
        "detected_at": "2026-09-01T11:45:00Z",
        "created_at": "2026-09-01T11:45:00Z",
    },
]


@router.get("/alerts", response_model=list[AlertRead])
def list_alerts(
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role(["VIEWER"])),
) -> list[AlertRead]:
    try:
        alerts = AlertRepository(db).list()
        return [AlertRead.model_validate(alert) for alert in alerts]
    except SQLAlchemyError:
        return [AlertRead.model_validate(alert) for alert in FALLBACK_ALERTS]


@router.get("/assets/{asset_id}/alerts", response_model=list[AlertRead])
def list_asset_alerts(
    asset_id: int,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role(["VIEWER"])),
) -> list[AlertRead]:
    try:
        alerts = AlertRepository(db).list_for_asset(asset_id)
        return [AlertRead.model_validate(alert) for alert in alerts]
    except SQLAlchemyError:
        matched = [a for a in FALLBACK_ALERTS if a["asset_id"] == asset_id]
        return [AlertRead.model_validate(alert) for alert in matched]


@router.patch("/alerts/{alert_id}", response_model=AlertRead)
def update_alert_status(
    alert_id: int,
    payload: AlertUpdate,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role(["OPERATOR", "ADMIN"])),
) -> AlertRead:
    new_status = payload.status.value if isinstance(payload.status, AlertStatus) else str(payload.status).upper()
    try:
        alert = AlertRepository(db).update_status(alert_id, new_status)
        if alert is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
        return AlertRead.model_validate(alert)
    except SQLAlchemyError:
        for a in FALLBACK_ALERTS:
            if a["id"] == alert_id:
                a["status"] = new_status
                return AlertRead.model_validate(a)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")


