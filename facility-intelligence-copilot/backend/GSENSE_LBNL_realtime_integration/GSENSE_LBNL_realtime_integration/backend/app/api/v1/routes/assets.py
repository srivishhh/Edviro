from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetRead, AssetUpdate

router = APIRouter()


@router.get("/assets", response_model=list[AssetRead])
def list_assets(db: Session = Depends(get_db)) -> list[AssetRead]:
    assets = db.query(Asset).all()
    return [AssetRead.model_validate(asset) for asset in assets]


@router.get("/assets/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: int, db: Session = Depends(get_db)) -> AssetRead:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return AssetRead.model_validate(asset)


@router.post("/assets", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db)) -> AssetRead:
    asset = Asset(**payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return AssetRead.model_validate(asset)


@router.put("/assets/{asset_id}", response_model=AssetRead)
def update_asset(asset_id: int, payload: AssetUpdate, db: Session = Depends(get_db)) -> AssetRead:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)

    db.commit()
    db.refresh(asset)
    return AssetRead.model_validate(asset)


@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(asset_id: int, db: Session = Depends(get_db)) -> None:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    db.delete(asset)
    db.commit()
    return None
