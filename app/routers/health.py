import structlog
from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.database import async_engine, get_redis
from app.schemas.common import HealthResponse

router = APIRouter()
logger = structlog.get_logger()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    db_status = "ok"
    redis_status = "ok"

    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error("health.db_check_failed", error=str(e))
        db_status = "error"

    try:
        redis = get_redis()
        await redis.ping()
        await redis.aclose()
    except Exception as e:
        logger.error("health.redis_check_failed", error=str(e))
        redis_status = "error"

    status = "healthy" if db_status == "ok" and redis_status == "ok" else "degraded"
    return HealthResponse(status=status, database=db_status, redis=redis_status, version=__version__)
