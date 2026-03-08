import pytest

from app.ai.base import AIResponse
from app.config import settings
from app.routers import assistant as assistant_router


class FakeProvider:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def generate(self, prompt: str, system: str | None = None, max_tokens: int = 4096) -> AIResponse:
        self.calls.append({"prompt": prompt, "system": system, "max_tokens": max_tokens})
        return AIResponse(content="Server-side answer", model="fake-model")


@pytest.mark.asyncio
async def test_assistant_chat_requires_server_configuration(client, monkeypatch):
    monkeypatch.setattr(settings, "AI_API_KEY", "")

    response = await client.post(
        "/api/v1/assistant/chat",
        json={"messages": [{"role": "user", "text": "Can I build here?"}]},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "AI assistant is not configured on the server"


@pytest.mark.asyncio
async def test_assistant_chat_uses_backend_provider(client, monkeypatch):
    fake_provider = FakeProvider()
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    monkeypatch.setattr(assistant_router, "get_ai_provider", lambda: fake_provider)

    response = await client.post(
        "/api/v1/assistant/chat",
        json={
            "messages": [
                {"role": "assistant", "text": "How can I help?"},
                {"role": "user", "text": "What setbacks apply?"},
            ],
            "parcel_context": "Current parcel: 123 King St W, Zoning: CR 3.0",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Server-side answer",
        "model_update": None,
        "proposed_action": None,
    }
    assert len(fake_provider.calls) == 1
    assert "Current site context:\nCurrent parcel: 123 King St W, Zoning: CR 3.0" in fake_provider.calls[0]["prompt"]
    assert "User: What setbacks apply?" in fake_provider.calls[0]["prompt"]
    assert fake_provider.calls[0]["system"] == assistant_router.SYSTEM_PROMPT
    assert fake_provider.calls[0]["max_tokens"] == 1500
