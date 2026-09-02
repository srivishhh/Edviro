from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.facility import Alert


class AlertRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[Alert]:
        return self.db.query(Alert).order_by(Alert.detected_at.desc()).all()

    def list_for_asset(self, asset_id: int) -> list[Alert]:
        return self.db.query(Alert).filter(Alert.asset_id == asset_id).order_by(Alert.detected_at.desc()).all()

    def create(self, **kwargs: object) -> Alert:
        alert = Alert(**kwargs)
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def upsert_open_alert(self, *, asset_id: int, alert_type: str, severity: str, message: str, anomaly_score: float) -> Alert:
        existing = (
            self.db.query(Alert)
            .filter(Alert.asset_id == asset_id, Alert.alert_type == alert_type, Alert.status == "OPEN")
            .order_by(Alert.detected_at.desc())
            .first()
        )
        if existing is not None:
            existing.severity = severity
            existing.message = message
            existing.anomaly_score = anomaly_score
            existing.detected_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        return self.create(
            asset_id=asset_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            anomaly_score=anomaly_score,
            detected_at=datetime.now(timezone.utc),
            status="OPEN",
        )

    def update_status(self, alert_id: int, status: str) -> Alert | None:
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if alert is None:
            return None
        alert.status = status
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def resolve_open_alerts_for_asset(self, asset_id: int, active_alert_types: set[str] | None = None) -> list[Alert]:
        """Resolves open alerts that are no longer active, preserving historical alert records."""
        active_types = active_alert_types or set()
        open_alerts = (
            self.db.query(Alert)
            .filter(Alert.asset_id == asset_id, Alert.status == "OPEN")
            .all()
        )
        resolved = []
        for alert in open_alerts:
            if alert.alert_type not in active_types:
                alert.status = "RESOLVED"
                resolved.append(alert)
        if resolved:
            self.db.commit()
            for r in resolved:
                self.db.refresh(r)
        return resolved
