import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.models.geospatial import ProjectParcel
from app.models.tenant import Project
from app.schemas.tenant import AddParcelRequest, ProjectCreate, ProjectResponse

router = APIRouter()


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    project = Project(
        name=body.name,
        description=body.description,
        organization_id=user["organization_id"],
        created_by=user["id"],
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(Project.organization_id == user["organization_id"]).order_by(Project.created_at.desc())
    )
    return result.scalars().all()


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.organization_id == user["organization_id"])
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.organization_id == user["organization_id"])
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.name = body.name
    if body.description is not None:
        project.description = body.description
    await db.flush()
    await db.refresh(project)
    return project


@router.post("/projects/{project_id}/parcels", status_code=status.HTTP_201_CREATED)
async def add_parcel_to_project(
    project_id: uuid.UUID,
    body: AddParcelRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    link = ProjectParcel(project_id=project_id, parcel_id=body.parcel_id, role=body.role)
    db.add(link)
    await db.flush()
    return {"status": "added", "project_id": str(project_id), "parcel_id": str(body.parcel_id)}


@router.delete("/projects/{project_id}/parcels/{parcel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_parcel_from_project(
    project_id: uuid.UUID,
    parcel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(ProjectParcel).where(ProjectParcel.project_id == project_id, ProjectParcel.parcel_id == parcel_id)
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Parcel not linked to project")
    await db.delete(link)
