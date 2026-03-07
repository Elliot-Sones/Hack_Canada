import json

import httpx
import structlog

from app.ai.base import AIProvider, AIResponse

logger = structlog.get_logger()


class ClaudeProvider(AIProvider):
    """Anthropic Claude API provider."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"

    async def generate(self, prompt: str, system: str | None = None, max_tokens: int = 4096) -> AIResponse:
        messages = [{"role": "user", "content": prompt}]
        payload = {"model": self.model, "max_tokens": max_tokens, "messages": messages}
        if system:
            payload["system"] = system

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()

        return AIResponse(
            content=data["content"][0]["text"],
            model=data.get("model", self.model),
            usage={
                "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                "output_tokens": data.get("usage", {}).get("output_tokens", 0),
            },
            raw_response=data,
        )

    async def generate_structured(
        self, prompt: str, schema: dict, system: str | None = None, max_tokens: int = 4096
    ) -> dict:
        system_msg = (system or "") + (
            "\n\nYou must respond with valid JSON matching this schema. "
            "Output ONLY the JSON, no markdown or explanation.\n"
            f"Schema: {json.dumps(schema)}"
        )
        response = await self.generate(prompt, system=system_msg.strip(), max_tokens=max_tokens)
        text = response.content.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
        return json.loads(text.strip())

    async def embed(self, text: str) -> list[float]:
        # Claude doesn't have an embeddings API — fall back to Voyage or raise
        raise NotImplementedError(
            "Claude does not provide an embeddings endpoint. "
            "Use a dedicated embedding provider (Voyage, OpenAI, or local model)."
        )
