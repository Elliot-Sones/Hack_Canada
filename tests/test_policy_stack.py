import uuid

import pytest

from app.dependencies import get_db_session
from app.main import app


@pytest.mark.anyio
async def test_parcel_policy_stack_returns_404_when_parcel_missing(client, monkeypatch):
    async def override_db():
        yield object()

    async def fake_list_active_snapshot_ids(_db, _snapshot_type):
        return []

    async def fake_get_active_parcel_by_id(_db, _parcel_id, active_snapshot_ids=None):
        assert active_snapshot_ids == []
        return None

    monkeypatch.setattr("app.routers.parcels.list_active_snapshot_ids", fake_list_active_snapshot_ids)
    monkeypatch.setattr("app.routers.parcels.get_active_parcel_by_id", fake_get_active_parcel_by_id)

    app.dependency_overrides[get_db_session] = override_db
    try:
        response = await client.get(f"/api/v1/parcels/{uuid.uuid4()}/policy-stack")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Parcel not found"


@pytest.mark.anyio
async def test_get_policy_stack_response_uses_thread_pool(monkeypatch):
    """Verify get_policy_stack_response dispatches the sync search to a thread."""
    from app.services import policy_stack as ps

    called_with = {}

    def fake_search(query, k):
        called_with["query"] = query
        called_with["k"] = k
        return []

    monkeypatch.setattr(ps, "_get_search", lambda: fake_search)

    parcel = type("P", (), {"id": uuid.uuid4(), "zone_code": "CR", "address": "1 King St", "current_use": None})()
    result = await ps.get_policy_stack_response(None, parcel)

    assert result.parcel_id == parcel.id
    assert called_with["k"] == 8
