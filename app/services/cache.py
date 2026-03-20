"""
Redis cache-aside helper for high-traffic parcel endpoints.

All Redis failures are silent — the app falls through to the DB query
exactly as if caching were disabled.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

KEY_PREFIX = "cocivil:"

_redis_pool: aioredis.Redis | None = None


async def get_async_redis() -> aioredis.Redis | None:
    """Return the module-level pooled async Redis client, creating it on first call."""
    global _redis_pool
    if _redis_pool is None:
        try:
            _redis_pool = aioredis.from_url(
                settings.REDIS_URL, decode_responses=True
            )
            await _redis_pool.ping()
            logger.info("Redis cache pool initialized")
        except Exception:
            logger.warning("Redis unavailable — caching disabled")
            _redis_pool = None
    return _redis_pool


async def get_or_fetch(
    key: str,
    fetch_fn: Callable[[], Awaitable[Any]],
    ttl: int = 86400,
) -> Any:
    """
    Cache-aside: return cached JSON if present, otherwise call *fetch_fn*,
    store the result in Redis, and return it.

    *key* should already include the ``cocivil:`` prefix.
    *ttl* is seconds (default 24 h).

    If Redis is unreachable or the cached value is corrupt, the function
    silently falls through to *fetch_fn* — the caller never sees an error.
    """
    r = await get_async_redis()

    # --- try cache hit ---
    if r is not None:
        try:
            cached = await r.get(key)
            if cached is not None:
                return json.loads(cached)
        except (aioredis.RedisError, ConnectionError):
            pass  # connection lost — fall through
        except Exception:
            # Corrupt cached value — delete so we don't re-hit it every request
            try:
                await r.delete(key)
            except Exception:
                pass

    # --- cache miss: fetch from DB ---
    result = await fetch_fn()

    # --- store in cache (best-effort) ---
    if r is not None:
        try:
            await r.set(key, json.dumps(result, default=str), ex=ttl)
        except Exception:
            pass  # Redis down mid-request — no problem

    return result
