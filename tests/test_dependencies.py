import uuid

import pytest
from fastapi import HTTPException
from jose import jwt

from app.config import settings
from starlette.requests import Request

from app.dependencies import get_current_user, get_optional_user
from app.models.tenant import User, WorkspaceMember


class ScalarOneResult:
    def __init__(self, row):
        self._row = row

    def scalar_one_or_none(self):
        return self._row


class ScalarsResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows


class DummyAsyncSession:
    def __init__(self, *results):
        self._results = iter(results)

    async def execute(self, _query):
        return next(self._results)


def _make_token(user_id: uuid.UUID, **claims) -> str:
    payload = {"sub": str(user_id), **claims}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _make_request() -> Request:
    return Request({"type": "http", "headers": [], "client": ("testclient", 50000)})


@pytest.mark.asyncio
async def test_get_current_user_uses_database_membership_role():
    user_id = uuid.uuid4()
    organization_id = uuid.uuid4()
    token = _make_token(user_id, role="owner")
    db = DummyAsyncSession(
        ScalarOneResult(User(id=user_id, email="user@example.com", name="Test User", is_active=True)),
        ScalarsResult([WorkspaceMember(user_id=user_id, organization_id=organization_id, role="analyst")]),
    )

    current_user = await get_current_user(request=_make_request(), authorization=f"Bearer {token}", db=db)

    assert current_user == {
        "id": user_id,
        "email": "user@example.com",
        "organization_id": organization_id,
        "role": "analyst",
    }


@pytest.mark.asyncio
async def test_get_current_user_requires_org_claim_for_multi_org_users():
    user_id = uuid.uuid4()
    token = _make_token(user_id)
    db = DummyAsyncSession(
        ScalarOneResult(User(id=user_id, email="user@example.com", name="Test User", is_active=True)),
        ScalarsResult(
            [
                WorkspaceMember(user_id=user_id, organization_id=uuid.uuid4(), role="analyst"),
                WorkspaceMember(user_id=user_id, organization_id=uuid.uuid4(), role="admin"),
            ]
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request=_make_request(), authorization=f"Bearer {token}", db=db)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Token must include organization_id when user belongs to multiple organizations"


@pytest.mark.asyncio
async def test_get_optional_user_passes_request_authorization_and_db_to_current_user():
    user_id = uuid.uuid4()
    organization_id = uuid.uuid4()
    token = _make_token(user_id)
    db = DummyAsyncSession(
        ScalarOneResult(User(id=user_id, email="user@example.com", name="Test User", is_active=True)),
        ScalarsResult([WorkspaceMember(user_id=user_id, organization_id=organization_id, role="analyst")]),
    )

    current_user = await get_optional_user(request=_make_request(), authorization=f"Bearer {token}", db=db)

    assert current_user == {
        "id": user_id,
        "email": "user@example.com",
        "organization_id": organization_id,
        "role": "analyst",
    }


@pytest.mark.asyncio
async def test_get_optional_user_returns_none_for_invalid_authorization_header():
    current_user = await get_optional_user(request=_make_request(), authorization="Bearer invalid-token", db=DummyAsyncSession())

    assert current_user is None
