from app.ai.base import AIProvider
from app.config import settings


def get_ai_provider() -> AIProvider:
    """Return the configured AI provider instance."""
    provider = settings.AI_PROVIDER.lower()

    if provider == "claude":
        from app.ai.claude_provider import ClaudeProvider
        return ClaudeProvider(api_key=settings.AI_API_KEY, model=settings.AI_MODEL)
    elif provider == "openai":
        from app.ai.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=settings.AI_API_KEY, model=settings.AI_MODEL)
    else:
        raise ValueError(f"Unknown AI provider: {provider}. Supported: claude, openai")
