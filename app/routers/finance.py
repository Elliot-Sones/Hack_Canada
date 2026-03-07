import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_db_session, get_optional_idempotency_key
from app.models.finance import FinancialRun
from app.schemas.common import JobAccepted
from app.schemas.finance import FinancialRunRequest, FinancialRunResponse
from app.tasks.finance import run_financial_analysis

router = APIRouter()


@router.post(
    "/scenarios/{scenario_id}/financial-runs", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED
)
async def create_financial_run(
    scenario_id: uuid.UUID,
    body: FinancialRunRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
    idempotency_key: str | None = Depends(get_optional_idempotency_key),
):
    run = FinancialRun(
        scenario_run_id=scenario_id,
        assumption_set_id=body.assumption_set_id,
        status="pending",
    )
    db.add(run)
    await db.flush()
    await db.refresh(run)

    run_financial_analysis.delay(str(run.id), str(scenario_id), body.parameters)

    return JobAccepted(
        job_id=run.id,
        status="accepted",
        location=f"{settings.API_V1_PREFIX}/financial-runs/{run.id}",
    )


@router.get("/financial-runs/{run_id}", response_model=FinancialRunResponse)
async def get_financial_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(FinancialRun).where(FinancialRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Financial run not found")
    return run
