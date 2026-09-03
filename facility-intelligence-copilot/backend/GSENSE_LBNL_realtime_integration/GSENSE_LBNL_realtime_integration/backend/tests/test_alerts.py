from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models.facility import Alert, Asset
from app.repositories.alerts import AlertRepository


def test_alert_creation_and_deduplication():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        asset = Asset(
            asset_code="HVAC-200",
            name="HVAC-200",
            asset_type="HVAC",
            status="warning",
            health_score=72.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(asset)
        session.commit()
        session.refresh(asset)

        repo = AlertRepository(session)
        first = repo.upsert_open_alert(
            asset_id=asset.id,
            alert_type="AIRFLOW_RESTRICTION",
            severity="WARNING",
            message="Airflow below baseline",
            anomaly_score=0.82,
        )
        second = repo.upsert_open_alert(
            asset_id=asset.id,
            alert_type="AIRFLOW_RESTRICTION",
            severity="WARNING",
            message="Airflow below baseline again",
            anomaly_score=0.86,
        )

        assert first.id == second.id
        assert session.query(Alert).filter(Alert.asset_id == asset.id).count() == 1
        assert second.status == "OPEN"


def test_alert_status_update():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        asset = Asset(
            asset_code="HVAC-201",
            name="HVAC-201",
            asset_type="HVAC",
            status="healthy",
            health_score=90.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(asset)
        session.commit()
        session.refresh(asset)

        repo = AlertRepository(session)
        alert = repo.create(
            asset_id=asset.id,
            alert_type="HIGH_TEMPERATURE",
            severity="WARNING",
            message="Temperature too high",
            anomaly_score=0.7,
            detected_at=datetime.now(timezone.utc),
            status="OPEN",
        )

        updated = repo.update_status(alert.id, "ACKNOWLEDGED")
        assert updated is not None
        assert updated.status == "ACKNOWLEDGED"
