import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entitlement import EntitlementResult, PrecedentSearch
from app.models.export import ExportJob
from app.models.finance import FinancialRun
from app.models.plan import DevelopmentPlan
from app.models.simulation import LayoutRun, Massing
from app.models.tenant import Project, ScenarioRun
from app.schemas.job import JobStatusResponse


def _serialize_job_status(job_type: str, row: object) -> JobStatusResponse:
    status_value = getattr(row, "status", None)
    if status_value is None and isinstance(row, EntitlementResult):
        status_value = row.overall_compliance
    return JobStatusResponse(
        job_id=row.id,
        job_type=job_type,
        status=status_value,
        started_at=getattr(row, "started_at", None),
        completed_at=getattr(row, "completed_at", None),
        result=(
            getattr(row, "result_json", None)
            or getattr(row, "output_json", None)
            or getattr(row, "results_json", None)
            or getattr(row, "applied_controls_json", None)
        ),
        error_message=getattr(row, "error_message", None),
    )


async def get_job_status(
    db: AsyncSession,
    job_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> JobStatusResponse | None:
    """Query across job tables while enforcing organization scoping."""
    queries = [
        (
            "scenario_run",
            select(ScenarioRun)
            .join(Project, Project.id == ScenarioRun.project_id)
            .where(ScenarioRun.id == job_id, Project.organization_id == organization_id),
        ),
        (
            "layout_run",
            select(LayoutRun)
            .join(Massing, Massing.id == LayoutRun.massing_id)
            .join(ScenarioRun, ScenarioRun.id == Massing.scenario_run_id)
            .join(Project, Project.id == ScenarioRun.project_id)
            .where(LayoutRun.id == job_id, Project.organization_id == organization_id),
        ),
        (
            "financial_run",
            select(FinancialRun)
            .join(ScenarioRun, ScenarioRun.id == FinancialRun.scenario_run_id)
            .join(Project, Project.id == ScenarioRun.project_id)
            .where(FinancialRun.id == job_id, Project.organization_id == organization_id),
        ),
        (
            "entitlement_result",
            select(EntitlementResult)
            .join(ScenarioRun, ScenarioRun.id == EntitlementResult.scenario_run_id)
            .join(Project, Project.id == ScenarioRun.project_id)
            .where(EntitlementResult.id == job_id, Project.organization_id == organization_id),
        ),
        (
            "precedent_search",
            select(PrecedentSearch)
            .join(ScenarioRun, ScenarioRun.id == PrecedentSearch.scenario_run_id)
            .join(Project, Project.id == ScenarioRun.project_id)
            .where(PrecedentSearch.id == job_id, Project.organization_id == organization_id),
        ),
        (
            "export_job",
            select(ExportJob)
            .join(Project, Project.id == ExportJob.project_id)
            .where(ExportJob.id == job_id, Project.organization_id == organization_id),
        ),
        (
            "development_plan",
            select(DevelopmentPlan).where(
                DevelopmentPlan.id == job_id,
                DevelopmentPlan.organization_id == organization_id,
            ),
        ),
    ]

    for job_type, query in queries:
        result = await db.execute(query)
        row = result.scalar_one_or_none()
        if row is not None:
            return _serialize_job_status(job_type, row)
    return None
