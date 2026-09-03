from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models.facility import Asset


def test_asset_model_round_trip():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        asset = Asset(
            asset_code="HVAC-999",
            name="HVAC-999",
            asset_type="HVAC",
            status="healthy",
            health_score=90.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(asset)
        session.commit()
        session.refresh(asset)

        assert asset.id is not None
        assert asset.asset_code == "HVAC-999"
