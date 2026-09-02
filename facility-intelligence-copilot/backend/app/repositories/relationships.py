from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.facility import AssetRelationship


class AssetRelationshipRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_asset(self, asset_id: int) -> list[AssetRelationship]:
        return (
            self.db.query(AssetRelationship)
            .filter(AssetRelationship.asset_id == asset_id)
            .order_by(AssetRelationship.id)
            .all()
        )

    def create(self, **kwargs: object) -> AssetRelationship:
        relationship = AssetRelationship(**kwargs)
        self.db.add(relationship)
        self.db.commit()
        self.db.refresh(relationship)
        return relationship
