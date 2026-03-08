import pytest
from types import SimpleNamespace

from app.dependencies import get_db_session
from app.main import app


@pytest.mark.asyncio
async def test_search_parcels_rejects_invalid_bbox(client):
    class DummySession:
        async def execute(self, *_args, **_kwargs):  # pragma: no cover - should never be reached
            raise AssertionError("execute should not be called for invalid bbox")

    async def override_db():
        yield DummySession()

    app.dependency_overrides[get_db_session] = override_db
    try:
        response = await client.get("/api/v1/parcels/search", params={"bbox": "bad,bounds"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_parcel_zoning_analysis_returns_backend_analysis(client, monkeypatch):
    parcel_id = "8b1f50d5-27f3-4865-a9d5-a2b444ecf0f8"

    class DummySession:
        async def execute(self, *_args, **_kwargs):  # pragma: no cover - route is fully monkeypatched
            raise AssertionError("execute should not be called")

    async def override_db():
        yield DummySession()

    async def fake_list_active_snapshot_ids(_db, snapshot_type):
        if snapshot_type == "parcel_base":
            return []
        if snapshot_type == "zoning_geometry":
            return ["zoning-snapshot"]
        raise AssertionError(f"unexpected snapshot type {snapshot_type}")

    async def fake_get_active_parcel_by_id(_db, requested_id, active_snapshot_ids=None):
        assert str(requested_id) == parcel_id
        assert active_snapshot_ids == []
        return SimpleNamespace(
            id=requested_id,
            address="123 King St W",
            zone_code="CR 3.0 (c2.0; r2.5) SS2 (x345)",
            lot_frontage_m=None,
            lot_depth_m=None,
        )

    async def fake_get_parcel_overlays_response(_db, parcel):
        return SimpleNamespace(
            overlays=[
                SimpleNamespace(
                    model_dump=lambda: {
                        "layer_type": "heritage",
                        "layer_name": "Heritage Conservation District",
                        "attributes_json": {},
                    }
                )
            ]
        )

    async def fake_get_active_zoning_assignment_count(*_args, **_kwargs):
        return 2

    monkeypatch.setattr("app.routers.parcels.list_active_snapshot_ids", fake_list_active_snapshot_ids)
    monkeypatch.setattr("app.routers.parcels.get_active_parcel_by_id", fake_get_active_parcel_by_id)
    monkeypatch.setattr("app.routers.parcels.get_parcel_overlays_response", fake_get_parcel_overlays_response)
    monkeypatch.setattr("app.routers.parcels._get_active_zoning_assignment_count", fake_get_active_zoning_assignment_count)

    app.dependency_overrides[get_db_session] = override_db
    try:
        response = await client.get(f"/api/v1/parcels/{parcel_id}/zoning-analysis")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["parcel_id"] == parcel_id
    assert payload["zone_string"] == "CR 3.0 (c2.0; r2.5) SS2 (x345)"
    assert payload["components"]["category"] == "CR"
    assert payload["standards"]["max_fsi"] == 3.0
    assert payload["standards"]["commercial_fsi"] == 2.0
    assert payload["standards"]["residential_fsi"] == 2.5
    assert payload["overlay_constraints"][0]["layer_type"] == "heritage"
    assert any("Site-specific exception" in warning for warning in payload["warnings"])
    assert any("Multiple zoning areas intersect this parcel" in warning for warning in payload["warnings"])
    assert any("Parcel frontage/depth data is missing" in warning for warning in payload["warnings"])
