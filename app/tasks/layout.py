import structlog

from app.worker import celery_app

logger = structlog.get_logger()


@celery_app.task(bind=True, name="app.tasks.layout.run_layout")
def run_layout(self, job_id: str, massing_id: str, params: dict | None = None):
    """Run unit mix / layout optimization for a massing.

    TODO: Implement LP-based layout optimization (OR-Tools):
    1. Load massing geometry and floor areas
    2. Load unit type library
    3. Optimize unit allocation per objective
    4. Store results and update job status
    """
    logger.info("layout.started", job_id=job_id, massing_id=massing_id)

    # TODO: Implement OR-Tools LP optimization
    # - Define decision variables (unit counts per type per floor)
    # - Revenue or density objective
    # - Area, parking, accessibility constraints
    # - Solve and extract allocation

    logger.info("layout.completed", job_id=job_id, massing_id=massing_id)
    return {"job_id": job_id, "status": "completed"}
