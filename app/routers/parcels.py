import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.models.geospatial import Parcel
from app.schemas.geospatial import ParcelDetailResponse, ParcelResponse, ParcelSearchParams, PolicyStackResponse

router = APIRouter()


@router.get("/parcels/search", response_model=list[ParcelResponse])
async def search_parcels(
    params: ParcelSearchParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
):
    query = select(Parcel)
    if params.address:
        query = query.where(Parcel.address.ilike(f"%{params.address}%"))
    if params.pin:
        query = query.where(Parcel.pin == params.pin)
    if params.zoning_code:
        query = query.where(Parcel.zone_code == params.zoning_code)
    query = query.offset((params.page - 1) * params.page_size).limit(params.page_size)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/parcels/{parcel_id}", response_model=ParcelDetailResponse)
async def get_parcel(
    parcel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(Parcel).where(Parcel.id == parcel_id))
    parcel = result.scalar_one_or_none()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return parcel


@router.get("/parcels/{parcel_id}/policy-stack", response_model=PolicyStackResponse)
async def get_parcel_policy_stack(parcel_id: uuid.UUID):
    # TODO: Implement policy stack resolution
    return PolicyStackResponse(parcel_id=parcel_id, applicable_policies=[], citations=[])


@router.get("/parcels/{parcel_id}/overlays")
async def get_parcel_overlays(parcel_id: uuid.UUID):
    # TODO: Implement overlay retrieval via spatial join
    return {"parcel_id": str(parcel_id), "overlays": []}
