"""Unit tests for app.services.cache — all Redis interactions are mocked."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.services.cache import get_or_fetch


@pytest.fixture(autouse=True)
def _reset_pool():
    """Ensure each test starts with a fresh pool state."""
    import app.services.cache as mod
    original = mod._redis_pool
    yield
    mod._redis_pool = original


def _make_redis_mock(get_return=None):
    r = AsyncMock()
    r.ping = AsyncMock()
    r.get = AsyncMock(return_value=get_return)
    r.set = AsyncMock()
    return r


async def test_get_or_fetch_cache_hit():
    """Cached value is returned; fetch_fn is never called."""
    cached = {"id": "abc", "address": "100 King St W"}
    r = _make_redis_mock(get_return=json.dumps(cached))

    fetch_fn = AsyncMock()

    with patch("app.services.cache.get_async_redis", return_value=r):
        result = await get_or_fetch("cocivil:parcel:abc", fetch_fn, ttl=86400)

    assert result == cached
    fetch_fn.assert_not_awaited()


async def test_get_or_fetch_cache_miss():
    """On miss, fetch_fn is called, result stored in Redis, and returned."""
    fresh = {"id": "xyz", "zone_code": "CR 3.0"}
    r = _make_redis_mock(get_return=None)

    fetch_fn = AsyncMock(return_value=fresh)

    with patch("app.services.cache.get_async_redis", return_value=r):
        result = await get_or_fetch("cocivil:zoning:xyz", fetch_fn, ttl=86400)

    assert result == fresh
    fetch_fn.assert_awaited_once()
    r.set.assert_awaited_once()
    stored_value = r.set.call_args[0][1]
    assert json.loads(stored_value) == fresh


async def test_get_or_fetch_redis_down():
    """When Redis is unavailable, fetch_fn is called as fallback."""
    fresh = {"id": "123", "overlays": []}
    fetch_fn = AsyncMock(return_value=fresh)

    with patch("app.services.cache.get_async_redis", return_value=None):
        result = await get_or_fetch("cocivil:overlays:123", fetch_fn, ttl=86400)

    assert result == fresh
    fetch_fn.assert_awaited_once()


async def test_get_or_fetch_fetch_raises():
    """If fetch_fn raises, the exception propagates and nothing is cached."""
    r = _make_redis_mock(get_return=None)

    fetch_fn = AsyncMock(side_effect=ValueError("DB error"))

    with patch("app.services.cache.get_async_redis", return_value=r):
        with pytest.raises(ValueError, match="DB error"):
            await get_or_fetch("cocivil:parcel:bad", fetch_fn, ttl=86400)

    r.set.assert_not_awaited()


async def test_get_or_fetch_ttl_applied():
    """TTL is passed through to Redis SET."""
    r = _make_redis_mock(get_return=None)
    fetch_fn = AsyncMock(return_value={"policies": []})

    with patch("app.services.cache.get_async_redis", return_value=r):
        await get_or_fetch("cocivil:policy:abc", fetch_fn, ttl=3600)

    r.set.assert_awaited_once()
    assert r.set.call_args.kwargs.get("ex") == 3600
