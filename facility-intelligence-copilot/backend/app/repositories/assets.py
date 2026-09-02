from __future__ import annotations

from typing import TypeVar

from sqlalchemy.orm import Session

from app.models.asset import Asset

T = TypeVar("T", bound=Asset)


class AssetRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[Asset]:
        return self.db.query(Asset).order_by(Asset.id).all()

    def get_by_id(self, asset_id: int) -> Asset | None:
        return self.db.query(Asset).filter(Asset.id == asset_id).first()

    def get_by_code(self, asset_code: str) -> Asset | None:
        return self.db.query(Asset).filter(Asset.asset_code == asset_code).first()

    def create(self, **kwargs: object) -> Asset:
        asset = Asset(**kwargs)
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def update(self, asset: Asset, **kwargs: object) -> Asset:
        for field, value in kwargs.items():
            setattr(asset, field, value)
        self.db.commit()
        self.db.refresh(asset)
        return asset
