import uuid
from datetime import date, datetime, timezone

import pytest

from app.dependencies import get_db_session
from app.main import app
from app.services.policy_stack import PolicyStackRecord, build_policy_stack_response, get_policy_zone_tokens


def test_build_policy_stack_response_orders_by_precedence_and_deduplicates_snapshots():
    parcel_id = uuid.uuid4()
    shared_snapshot_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    lower_precedence = PolicyStackRecord(
        clause_id=uuid.uuid4(),
        policy_version_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_title="Base Zoning",
        doc_type="zoning_bylaw",
        override_level=4,
        section_ref="40.10.40.10",
        page_ref="12",
        raw_text="Base height is 30 metres.",
        normalized_type="max_height",
        normalized_json={"value": 30, "unit": "m"},
        applicability_json={},
        confidence=0.98,
        effective_date=date(2026, 1, 1),
        source_url="https://example.com/base",
        snapshot_id=shared_snapshot_id,
        snapshot_type="policy",
        snapshot_label="policy-v1",
        snapshot_published_at=now,
    )
    higher_precedence = PolicyStackRecord(
        clause_id=uuid.uuid4(),
        policy_version_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_title="Site Specific Exception",
        doc_type="site_specific",
        override_level=1,
        section_ref="SSA-1",
        page_ref="2",
        raw_text="Site-specific height is 36 metres.",
        normalized_type="max_height",
        normalized_json={"value": 36, "unit": "m"},
        applicability_json={"lot": "specific"},
        confidence=0.99,
        effective_date=date(2026, 2, 1),
        source_url="https://example.com/site-specific",
        snapshot_id=shared_snapshot_id,
        snapshot_type="policy",
        snapshot_label="policy-v1",
        snapshot_published_at=now,
    )

    response = build_policy_stack_response(parcel_id, [lower_precedence, higher_precedence])

    assert response.parcel_id == parcel_id
    assert [entry.override_level for entry in response.applicable_policies] == [1, 4]
    assert response.applicable_policies[0].document_title == "Site Specific Exception"
    assert len(response.citations) == 2
    assert len(response.snapshots) == 1
    assert response.snapshots[0].version_label == "policy-v1"


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


def test_get_policy_zone_tokens_include_full_string_and_base_category():
    tokens = get_policy_zone_tokens("CR 3.0 (c2.0; r2.5) SS2 (x345)")

    assert tokens[0] == "CR 3.0 (c2.0; r2.5) SS2 (x345)"
    assert "CR" in tokens
