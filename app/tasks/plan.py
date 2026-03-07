import uuid
from datetime import datetime, timezone

import structlog

from app.database import get_sync_db
from app.models.plan import DevelopmentPlan, SubmissionDocument
from app.worker import celery_app

logger = structlog.get_logger()

PIPELINE_STEPS = [
    "query_parsing",
    "parcel_lookup",
    "policy_resolution",
    "massing_generation",
    "layout_optimization",
    "financial_analysis",
    "entitlement_check",
    "precedent_search",
    "document_generation",
]

SUBMISSION_DOCUMENTS = [
    {
        "doc_type": "cover_letter",
        "title": "Cover Letter",
        "description": "Introduction letter to the planning department summarizing the proposal",
        "sort_order": 1,
    },
    {
        "doc_type": "planning_rationale",
        "title": "Planning Rationale",
        "description": "Detailed justification for the proposed development with policy citations",
        "sort_order": 2,
    },
    {
        "doc_type": "compliance_matrix",
        "title": "Policy Compliance Matrix",
        "description": "Rule-by-rule comparison of proposal against applicable zoning provisions",
        "sort_order": 3,
    },
    {
        "doc_type": "site_plan_data",
        "title": "Site Plan Data Summary",
        "description": "Parcel geometry, setbacks, building footprint, access points, and key dimensions",
        "sort_order": 4,
    },
    {
        "doc_type": "massing_summary",
        "title": "Massing & Built Form Summary",
        "description": "Building envelope, height, storeys, GFA breakdown, and 3D massing parameters",
        "sort_order": 5,
    },
    {
        "doc_type": "unit_mix_summary",
        "title": "Unit Mix & Layout Summary",
        "description": "Unit count by type, area ranges, accessible units, and floor plate breakdown",
        "sort_order": 6,
    },
    {
        "doc_type": "financial_feasibility",
        "title": "Financial Feasibility Summary",
        "description": "High-level pro forma showing revenue, costs, NOI, cap rate, and return metrics",
        "sort_order": 7,
    },
    {
        "doc_type": "precedent_report",
        "title": "Precedent Analysis Report",
        "description": "Comparable approved developments nearby with outcomes and rationale excerpts",
        "sort_order": 8,
    },
    {
        "doc_type": "public_benefit_statement",
        "title": "Public Benefit Statement",
        "description": "Community contributions, affordable housing, public realm improvements",
        "sort_order": 9,
    },
    {
        "doc_type": "shadow_study",
        "title": "Shadow Study Data",
        "description": "Shadow impact analysis data for the proposed building envelope",
        "sort_order": 10,
    },
]


def _update_plan_status(db, plan, status, step=None, progress_update=None, error=None):
    """Helper to update plan status in the database."""
    plan.status = status
    if step:
        plan.current_step = step
    if progress_update:
        progress = plan.pipeline_progress or {}
        progress.update(progress_update)
        plan.pipeline_progress = progress
    if error:
        plan.error_message = error
    db.commit()
    db.refresh(plan)


@celery_app.task(bind=True, name="app.tasks.plan.run_plan_generation")
def run_plan_generation(self, plan_id: str, query: str, auto_run: bool = True):
    """Orchestrate the full plan generation pipeline.

    Pipeline steps:
    1. Parse query → structured development parameters (via AI)
    2. Look up parcel by address
    3. Resolve applicable policy stack
    4. Generate building massing
    5. Optimize unit mix / layout
    6. Run financial pro forma
    7. Check entitlement compliance
    8. Search precedent applications
    9. Generate submission documents (via AI)
    """
    logger.info("plan.generation.started", plan_id=plan_id)

    db = get_sync_db()
    try:
        plan = db.query(DevelopmentPlan).filter(DevelopmentPlan.id == uuid.UUID(plan_id)).one()
        plan.started_at = datetime.now(timezone.utc)

        # Initialize pipeline progress
        plan.pipeline_progress = {step: "pending" for step in PIPELINE_STEPS}
        _update_plan_status(db, plan, "running_pipeline", step="query_parsing",
                           progress_update={"query_parsing": "running"})

        # --- Step 1: Query Parsing ---
        # TODO: Call AI provider to parse the query
        # from app.ai.factory import get_ai_provider
        # from app.ai.query_parser import parse_development_query
        # provider = get_ai_provider()
        # parsed = await parse_development_query(provider, query)
        # plan.parsed_parameters = parsed
        # plan.parse_confidence = parsed.get("confidence", 0.0)

        # For now, store raw query as placeholder
        plan.parsed_parameters = {"raw_query": query, "status": "stub_parse"}
        plan.parse_confidence = 0.0
        _update_plan_status(db, plan, "running_pipeline", step="parcel_lookup",
                           progress_update={"query_parsing": "completed", "parcel_lookup": "running"})

        # --- Step 2: Parcel Lookup ---
        # TODO: Search parcels table by address from parsed parameters
        _update_plan_status(db, plan, "running_pipeline", step="policy_resolution",
                           progress_update={"parcel_lookup": "completed", "policy_resolution": "running"})

        # --- Step 3: Policy Resolution ---
        # TODO: Resolve policy stack for the parcel + jurisdiction
        _update_plan_status(db, plan, "running_pipeline", step="massing_generation",
                           progress_update={"policy_resolution": "completed", "massing_generation": "running"})

        # --- Step 4: Massing Generation ---
        # TODO: Generate building envelope within policy constraints
        _update_plan_status(db, plan, "running_pipeline", step="layout_optimization",
                           progress_update={"massing_generation": "completed", "layout_optimization": "running"})

        # --- Step 5: Layout Optimization ---
        # TODO: Optimize unit mix
        _update_plan_status(db, plan, "running_pipeline", step="financial_analysis",
                           progress_update={"layout_optimization": "completed", "financial_analysis": "running"})

        # --- Step 6: Financial Analysis ---
        # TODO: Run pro forma
        _update_plan_status(db, plan, "running_pipeline", step="entitlement_check",
                           progress_update={"financial_analysis": "completed", "entitlement_check": "running"})

        # --- Step 7: Entitlement Check ---
        # TODO: Check compliance
        _update_plan_status(db, plan, "running_pipeline", step="precedent_search",
                           progress_update={"entitlement_check": "completed", "precedent_search": "running"})

        # --- Step 8: Precedent Search ---
        # TODO: Find comparable applications
        _update_plan_status(db, plan, "running_pipeline", step="document_generation",
                           progress_update={"precedent_search": "completed", "document_generation": "running"})

        # --- Step 9: Generate Submission Documents ---
        for doc_spec in SUBMISSION_DOCUMENTS:
            doc = SubmissionDocument(
                plan_id=plan.id,
                doc_type=doc_spec["doc_type"],
                title=doc_spec["title"],
                description=doc_spec["description"],
                sort_order=doc_spec["sort_order"],
                format="markdown",
                status="pending",
                # TODO: Generate actual content via AI provider
                content_text=f"# {doc_spec['title']}\n\n*Content generation pending — "
                             f"this document will be generated by the AI provider using "
                             f"analysis results from the pipeline.*\n",
            )
            doc.status = "completed"
            db.add(doc)
        db.flush()

        # Mark complete
        plan.pipeline_progress = {step: "completed" for step in PIPELINE_STEPS}
        plan.current_step = None
        plan.completed_at = datetime.now(timezone.utc)
        plan.summary = {
            "pipeline_steps_completed": len(PIPELINE_STEPS),
            "documents_generated": len(SUBMISSION_DOCUMENTS),
            "status": "All pipeline steps and documents completed (stub implementations)",
        }
        _update_plan_status(db, plan, "completed")

        logger.info("plan.generation.completed", plan_id=plan_id)
        return {"plan_id": plan_id, "status": "completed"}

    except Exception as e:
        logger.error("plan.generation.failed", plan_id=plan_id, error=str(e))
        try:
            plan = db.query(DevelopmentPlan).filter(DevelopmentPlan.id == uuid.UUID(plan_id)).one()
            _update_plan_status(db, plan, "failed", error=str(e))
        except Exception:
            pass
        raise
    finally:
        db.close()
