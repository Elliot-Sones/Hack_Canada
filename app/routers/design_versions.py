"""Design version control API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.schemas.design_version import BranchCreate, BranchResponse, CommitRequest, VersionResponse
from app.services import design_version_service as dvs

router = APIRouter(prefix="/designs")


@router.post("/{project_id}/branches", response_model=BranchResponse, status_code=201)
async def create_branch(
    project_id: uuid.UUID,
    body: BranchCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    branch = await dvs.create_branch(
        db,
        project_id=project_id,
        name=body.name,
        organization_id=user["organization_id"],
        user_id=user["id"],
        from_version_id=body.from_version_id,
    )
    return BranchResponse(
        id=branch.id,
        project_id=branch.project_id,
        name=branch.name,
        created_by=branch.created_by,
        created_at=branch.created_at,
    )


@router.get("/{project_id}/branches", response_model=list[BranchResponse])
async def list_branches(
    project_id: uuid.UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    branches = await dvs.list_branches(db, project_id)
    return [
        BranchResponse(
            id=b.id, project_id=b.project_id, name=b.name,
            created_by=b.created_by, created_at=b.created_at,
        )
        for b in branches
    ]


@router.delete("/{project_id}/branches/{branch_id}", status_code=204)
async def delete_branch(
    project_id: uuid.UUID,
    branch_id: uuid.UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    await dvs.delete_branch(db, branch_id)


@router.post("/branches/{branch_id}/commit", response_model=VersionResponse, status_code=201)
async def commit_version(
    branch_id: uuid.UUID,
    body: CommitRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    version = await dvs.commit_version(
        db,
        branch_id=branch_id,
        floor_plans=body.floor_plans,
        model_params=body.model_params,
        message=body.message,
        user_id=user["id"],
        parcel_id=body.parcel_id,
    )
    return VersionResponse(
        id=version.id,
        branch_id=version.branch_id,
        version_number=version.version_number,
        floor_plans=version.floor_plans,
        model_params=version.model_params,
        compliance_status=version.compliance_status,
        compliance_details=version.compliance_details,
        variance_items=version.variance_items,
        blocking_issues=version.blocking_issues,
        message=version.message,
        change_summary=version.change_summary,
        created_by=version.created_by,
        created_at=version.created_at,
    )


@router.get("/branches/{branch_id}/versions", response_model=list[VersionResponse])
async def list_versions_endpoint(
    branch_id: uuid.UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    versions = await dvs.list_versions(db, branch_id)
    return [
        VersionResponse(
            id=v.id, branch_id=v.branch_id, version_number=v.version_number,
            compliance_status=v.compliance_status, compliance_details=v.compliance_details,
            variance_items=v.variance_items, blocking_issues=v.blocking_issues,
            message=v.message, change_summary=v.change_summary,
            created_by=v.created_by, created_at=v.created_at,
        )
        for v in versions
    ]


@router.get("/branches/{branch_id}/latest", response_model=VersionResponse | None)
async def get_latest_version(
    branch_id: uuid.UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    version = await dvs.get_latest(db, branch_id)
    if not version:
        return None
    return VersionResponse(
        id=version.id, branch_id=version.branch_id, version_number=version.version_number,
        floor_plans=version.floor_plans, model_params=version.model_params,
        compliance_status=version.compliance_status, compliance_details=version.compliance_details,
        variance_items=version.variance_items, blocking_issues=version.blocking_issues,
        message=version.message, change_summary=version.change_summary,
        created_by=version.created_by, created_at=version.created_at,
    )


@router.get("/versions/{version_id}", response_model=VersionResponse)
async def get_version(
    version_id: uuid.UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    version = await dvs.get_version(db, version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    return VersionResponse(
        id=version.id, branch_id=version.branch_id, version_number=version.version_number,
        floor_plans=version.floor_plans, model_params=version.model_params,
        compliance_status=version.compliance_status, compliance_details=version.compliance_details,
        variance_items=version.variance_items, blocking_issues=version.blocking_issues,
        message=version.message, change_summary=version.change_summary,
        created_by=version.created_by, created_at=version.created_at,
    )
