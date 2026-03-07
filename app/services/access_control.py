import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entitlement import EntitlementResult, PrecedentMatch, PrecedentSearch
from app.models.export import ExportJob
from app.models.finance import FinancialRun
from app.models.simulation import LayoutRun, Massing
from app.models.tenant import Project, ScenarioRun


def require_admin(user: dict) -> None:
    if user.get("role") not in {"owner", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


async def get_project_for_org(db: AsyncSession, project_id: uuid.UUID, organization_id: uuid.UUID) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.organization_id == organization_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def get_scenario_for_org(
    db: AsyncSession,
    scenario_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> ScenarioRun:
    result = await db.execute(
        select(ScenarioRun)
        .join(Project, Project.id == ScenarioRun.project_id)
        .where(ScenarioRun.id == scenario_id, Project.organization_id == organization_id)
    )
    scenario = result.scalar_one_or_none()
    if scenario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
    return scenario


async def get_massing_for_org(
    db: AsyncSession,
    massing_id: uuid.UUID,
    organization_id: uuid.UUID,
    *,
    load_template: bool = False,
) -> Massing:
    query = (
        select(Massing)
        .join(ScenarioRun, ScenarioRun.id == Massing.scenario_run_id)
        .join(Project, Project.id == ScenarioRun.project_id)
        .where(Massing.id == massing_id, Project.organization_id == organization_id)
    )
    if load_template:
        query = query.options(selectinload(Massing.template))
    result = await db.execute(query)
    massing = result.scalar_one_or_none()
    if massing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Massing not found")
    return massing


async def get_layout_run_for_org(db: AsyncSession, layout_run_id: uuid.UUID, organization_id: uuid.UUID) -> LayoutRun:
    result = await db.execute(
        select(LayoutRun)
        .join(Massing, Massing.id == LayoutRun.massing_id)
        .join(ScenarioRun, ScenarioRun.id == Massing.scenario_run_id)
        .join(Project, Project.id == ScenarioRun.project_id)
        .where(LayoutRun.id == layout_run_id, Project.organization_id == organization_id)
    )
    layout = result.scalar_one_or_none()
    if layout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layout run not found")
    return layout


async def get_financial_run_for_org(
    db: AsyncSession,
    run_id: uuid.UUID,
    organization_id: uuid.UUID,
    *,
    load_assumption_set: bool = False,
) -> FinancialRun:
    query = (
        select(FinancialRun)
        .join(ScenarioRun, ScenarioRun.id == FinancialRun.scenario_run_id)
        .join(Project, Project.id == ScenarioRun.project_id)
        .where(FinancialRun.id == run_id, Project.organization_id == organization_id)
    )
    if load_assumption_set:
        query = query.options(selectinload(FinancialRun.assumption_set))
    result = await db.execute(query)
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Financial run not found")
    return run


async def get_entitlement_result_for_org(
    db: AsyncSession,
    run_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> EntitlementResult:
    result = await db.execute(
        select(EntitlementResult)
        .join(ScenarioRun, ScenarioRun.id == EntitlementResult.scenario_run_id)
        .join(Project, Project.id == ScenarioRun.project_id)
        .where(EntitlementResult.id == run_id, Project.organization_id == organization_id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entitlement run not found")
    return run


async def get_precedent_search_for_org(
    db: AsyncSession,
    search_id: uuid.UUID,
    organization_id: uuid.UUID,
    *,
    load_matches: bool = False,
) -> PrecedentSearch:
    query = (
        select(PrecedentSearch)
        .join(ScenarioRun, ScenarioRun.id == PrecedentSearch.scenario_run_id)
        .join(Project, Project.id == ScenarioRun.project_id)
        .where(PrecedentSearch.id == search_id, Project.organization_id == organization_id)
    )
    if load_matches:
        query = query.options(selectinload(PrecedentSearch.matches).selectinload(PrecedentMatch.application))
    result = await db.execute(query)
    search = result.scalar_one_or_none()
    if search is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Precedent search not found")
    return search


async def get_export_job_for_org(db: AsyncSession, export_id: uuid.UUID, organization_id: uuid.UUID) -> ExportJob:
    result = await db.execute(
        select(ExportJob)
        .join(Project, Project.id == ExportJob.project_id)
        .where(ExportJob.id == export_id, Project.organization_id == organization_id)
    )
    export = result.scalar_one_or_none()
    if export is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
    return export
