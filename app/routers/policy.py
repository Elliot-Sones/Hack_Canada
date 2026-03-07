import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.schemas.policy import PolicySearchParams, PolicySearchResponse

router = APIRouter()


@router.get("/policies/search", response_model=PolicySearchResponse)
async def search_policies(
    params: PolicySearchParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
):
    # TODO: Implement full-text + semantic policy search
    return PolicySearchResponse(clauses=[], total=0, page=params.page, page_size=params.page_size)


@router.post("/scenarios/{scenario_id}/policy-overrides", status_code=status.HTTP_201_CREATED)
async def create_policy_override(
    scenario_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    # TODO: Store policy overrides for variance scenarios
    return {"scenario_id": str(scenario_id), "overrides": body, "status": "created"}
