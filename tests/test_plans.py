import pytest

from app.dependencies import get_db_session
from app.main import app


@pytest.mark.asyncio
async def test_generate_plan_requires_authentication(client):
    class DummySession:
        async def execute(self, *_args, **_kwargs):  # pragma: no cover - auth should fail first
            raise AssertionError("execute should not be called")

        async def flush(self):  # pragma: no cover - auth should fail first
            raise AssertionError("flush should not be called")

        async def refresh(self, *_args, **_kwargs):  # pragma: no cover - auth should fail first
            raise AssertionError("refresh should not be called")

        async def commit(self):  # pragma: no cover - auth should fail first
            raise AssertionError("commit should not be called")

        def add(self, *_args, **_kwargs):  # pragma: no cover - auth should fail first
            raise AssertionError("add should not be called")

    async def override_db():
        yield DummySession()

    app.dependency_overrides[get_db_session] = override_db
    try:
        response = await client.post(
            "/api/v1/plans/generate",
            json={"query": "Build a 6 storey mixed-use project at 123 King Street West", "auto_run": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authorization header"
