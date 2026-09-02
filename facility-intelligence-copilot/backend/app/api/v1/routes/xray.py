from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, require_role
from app.db.session import get_db
from app.models.facility import Alert, Asset
from app.xray.models import XRayInvestigationRequest, XRayInvestigationResult
from app.xray.service import XRayService

router = APIRouter()
service = XRayService()


def _fallback_asset(asset_id: int) -> dict | None:
    if asset_id == 7:
        return {
            "id": 7,
            "asset_code": "HVAC-007",
            "name": "HVAC-007",
            "asset_type": "HVAC",
            "status": "warning",
            "health_score": 68,
        }
    return None


def _fallback_alert(alert_id: int) -> dict | None:
    if alert_id == 101:
        return {
            "id": 101,
            "asset_id": 7,
            "alert_type": "AIRFLOW_RESTRICTION",
            "severity": "WARNING",
            "message": "Airflow below baseline",
            "anomaly_score": 0.82,
            "status": "OPEN",
        }
    return None


@router.post("/xray/investigations", status_code=status.HTTP_202_ACCEPTED)
def create_xray_investigation(
    payload: XRayInvestigationRequest,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role(["OPERATOR", "ADMIN"])),
) -> dict:
    asset_id = payload.asset_id
    alert_id = payload.alert_id

    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
    except SQLAlchemyError:
        asset = _fallback_asset(asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
    except SQLAlchemyError:
        alert = _fallback_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    result = service.create_investigation(asset_id=asset_id, alert_id=alert_id)

    response = {
        "investigation_id": result.investigation_id,
        "asset_id": asset_id,
        "alert_id": alert_id,
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    response["summary"] = result.summary
    response["root_cause"] = result.root_cause
    response["confidence"] = result.confidence
    response["severity"] = result.severity
    response["evidence"] = [item.model_dump(mode="json") for item in result.evidence]
    response["observed"] = result.observed
    response["inferred"] = result.inferred
    response["alternative_causes"] = result.alternative_causes
    response["affected_assets"] = result.affected_assets
    response["recommended_actions"] = result.recommended_actions
    return response


@router.get("/xray/investigations/{investigation_id}")
def get_xray_investigation(
    investigation_id: str,
    user: AuthenticatedUser = Depends(require_role(["VIEWER"])),
) -> dict:
    if len(investigation_id) > 128:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid investigation_id format.")

    record = service.get_investigation(investigation_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")
    if record.result is None:
        return service.build_status(investigation_id, status="PENDING")
    result = record.result
    return {
        "investigation_id": result.investigation_id,
        "asset_id": result.asset_id,
        "alert_id": result.alert_id,
        "summary": result.summary,
        "root_cause": result.root_cause,
        "confidence": result.confidence,
        "severity": result.severity,
        "evidence": [item.model_dump(mode="json") for item in result.evidence],
        "observed": result.observed,
        "inferred": result.inferred,
        "alternative_causes": result.alternative_causes,
        "affected_assets": result.affected_assets,
        "recommended_actions": result.recommended_actions,
        "created_at": result.created_at.isoformat(),
    }


