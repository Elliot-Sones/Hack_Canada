from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AIResponse:
    """Standardized response from any AI provider."""
    content: str
    model: str
    usage: dict = field(default_factory=dict)
    raw_response: dict | None = None


class AIProvider(ABC):
    """Abstract interface for LLM providers. Swap Claude, OpenAI, or any other."""

    @abstractmethod
    async def generate(self, prompt: str, system: str | None = None, max_tokens: int = 4096) -> AIResponse:
        """Generate a text completion."""
        ...

    @abstractmethod
    async def generate_structured(
        self, prompt: str, schema: dict, system: str | None = None, max_tokens: int = 4096
    ) -> dict:
        """Generate a response conforming to a JSON schema.

        Returns parsed dict matching the schema.
        """
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""
        ...
