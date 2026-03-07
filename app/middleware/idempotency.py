import hashlib
import json

from fastapi import HTTPException, status

from app.database import get_redis

IDEMPOTENCY_TTL = 86400  # 24 hours


async def check_idempotency(key: str | None, response_body: dict | None = None) -> dict | None:
    """
    Check if an idempotency key has been seen before.
    If response_body is provided, cache it for the key.
    Returns cached response if key was already used, None otherwise.
    """
    if not key:
        return None

    redis = get_redis()
    cache_key = f"idempotency:{hashlib.sha256(key.encode()).hexdigest()}"

    try:
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        if response_body is not None:
            await redis.set(cache_key, json.dumps(response_body), ex=IDEMPOTENCY_TTL)
    except Exception:
        pass
    finally:
        await redis.aclose()

    return None


async def enforce_idempotency(key: str | None) -> dict | None:
    """FastAPI dependency: returns cached response or None."""
    if not key:
        return None

    cached = await check_idempotency(key)
    if cached:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Duplicate request", "cached_response": cached},
        )
    return None
