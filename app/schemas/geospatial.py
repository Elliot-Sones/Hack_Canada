import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ParcelSearchParams(BaseModel):
    address: str | None = None
    pin: str | None = None
    zoning_code: str | None = None
    min_lot_area: float | None = None
    max_lot_area: float | None = None
    min_frontage: float | None = None
    bbox: str | None = Field(None, description="Bounding box as 'minx,miny,maxx,maxy'")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ParcelResponse(BaseModel):
    id: uuid.UUID
    jurisdiction_id: uuid.UUID
    pin: str | None = None
    address: str | None = None
    lot_area_m2: float | None = None
    lot_frontage_m: float | None = None
    zone_code: str | None = None
    current_use: str | None = None

    model_config = {"from_attributes": True}


class ParcelDetailResponse(ParcelResponse):
    lot_depth_m: float | None = None
    assessed_value: float | None = None
    created_at: datetime | None = None


class PolicyStackResponse(BaseModel):
    parcel_id: uuid.UUID
    applicable_policies: list[dict] = []
    citations: list[dict] = []
