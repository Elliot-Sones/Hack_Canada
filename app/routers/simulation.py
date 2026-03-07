import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_db_session, get_optional_idempotency_key
from app.models.simulation import LayoutRun, Massing
from app.schemas.common import JobAccepted
from app.schemas.simulation import LayoutRunRequest, LayoutRunResponse, MassingRequest, MassingResponse
from app.tasks.layout import run_layout
from app.tasks.massing import run_massing

router = APIRouter()


@router.post("/scenarios/{scenario_id}/massings", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_massing(
    scenario_id: uuid.UUID,
    body: MassingRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
    idempotency_key: str | None = Depends(get_optional_idempotency_key),
):
    massing = Massing(scenario_run_id=scenario_id, template_id=body.template_id)
    db.add(massing)
    await db.flush()
    await db.refresh(massing)

    run_massing.delay(str(massing.id), str(scenario_id), body.parameters)

    return JobAccepted(
        job_id=massing.id,
        status="accepted",
        location=f"{settings.API_V1_PREFIX}/massings/{massing.id}",
    )


@router.get("/massings/{massing_id}", response_model=MassingResponse)
async def get_massing(
    massing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(Massing).where(Massing.id == massing_id))
    massing = result.scalar_one_or_none()
    if not massing:
        raise HTTPException(status_code=404, detail="Massing not found")
    return massing


@router.post("/massings/{massing_id}/layout-runs", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_layout_run(
    massing_id: uuid.UUID,
    body: LayoutRunRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
    idempotency_key: str | None = Depends(get_optional_idempotency_key),
):
    layout = LayoutRun(
        massing_id=massing_id,
        objective=body.optimization_objective,
        status="pending",
    )
    db.add(layout)
    await db.flush()
    await db.refresh(layout)

    run_layout.delay(str(layout.id), str(massing_id), body.parameters)

    return JobAccepted(
        job_id=layout.id,
        status="accepted",
        location=f"{settings.API_V1_PREFIX}/layout-runs/{layout.id}",
    )


@router.get("/layout-runs/{layout_run_id}", response_model=LayoutRunResponse)
async def get_layout_run(
    layout_run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(LayoutRun).where(LayoutRun.id == layout_run_id))
    layout = result.scalar_one_or_none()
    if not layout:
        raise HTTPException(status_code=404, detail="Layout run not found")
    return layout
