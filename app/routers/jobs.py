import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.schemas.job import JobStatusResponse
from app.services.job_service import get_job_status

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    result = await get_job_status(db, job_id, user["organization_id"])
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return result
