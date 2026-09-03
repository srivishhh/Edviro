from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.facility import Alert
from app.repositories.alerts import AlertRepository
from app.schemas.alert import AlertRead, AlertUpdate

router = APIRouter()


@router.get("/alerts", response_model=list[AlertRead])
def list_alerts(db: Session = Depends(get_db)) -> list[AlertRead]:
    alerts = AlertRepository(db).list()
    return [AlertRead.model_validate(alert) for alert in alerts]


@router.get("/assets/{asset_id}/alerts", response_model=list[AlertRead])
def list_asset_alerts(asset_id: int, db: Session = Depends(get_db)) -> list[AlertRead]:
    alerts = AlertRepository(db).list_for_asset(asset_id)
    return [AlertRead.model_validate(alert) for alert in alerts]


@router.patch("/alerts/{alert_id}", response_model=AlertRead)
def update_alert_status(alert_id: int, payload: AlertUpdate, db: Session = Depends(get_db)) -> AlertRead:
    alert = AlertRepository(db).update_status(alert_id, payload.status.upper())
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return AlertRead.model_validate(alert)
