import json

import httpx
import structlog

from app.ai.base import AIProvider, AIResponse

logger = structlog.get_logger()


class OpenAIProvider(AIProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o", embedding_model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self.embedding_model = embedding_model
        self.base_url = "https://api.openai.com/v1"

    async def generate(self, prompt: str, system: str | None = None, max_tokens: int = 4096) -> AIResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": self.model, "max_tokens": max_tokens, "messages": messages}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]
        return AIResponse(
            content=choice["message"]["content"],
            model=data.get("model", self.model),
            usage={
                "input_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                "output_tokens": data.get("usage", {}).get("completion_tokens", 0),
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
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
        return json.loads(text.strip())

    async def embed(self, text: str) -> list[float]:
        payload = {"model": self.embedding_model, "input": text}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        return data["data"][0]["embedding"]
