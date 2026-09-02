from datetime import datetime

from pydantic import BaseModel, Field


class AssetBase(BaseModel):
    asset_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=150)
    asset_type: str = Field(..., min_length=1, max_length=50)
    building_id: int | None = None
    floor_id: int | None = None
    manufacturer: str | None = None
    model: str | None = None
    installation_date: datetime | None = None
    status: str = "healthy"
    health_score: float = 100.0


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    asset_code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    asset_type: str | None = Field(default=None, min_length=1, max_length=50)
    building_id: int | None = None
    floor_id: int | None = None
    manufacturer: str | None = None
    model: str | None = None
    installation_date: datetime | None = None
    status: str | None = None
    health_score: float | None = None


class AssetRead(AssetBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
