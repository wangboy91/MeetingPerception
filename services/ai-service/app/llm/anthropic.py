from typing import Any

import httpx

from app.core.config import LlmSettings
from app.llm.base import LlmProvider
from app.llm.json_utils import parse_json_object


class AnthropicProvider(LlmProvider):
    def __init__(self, settings: LlmSettings) -> None:
        self.settings = settings

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        del schema
        async with httpx.AsyncClient(timeout=self.settings.timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.base_url}/v1/messages",
                headers={
                    "x-api-key": self.settings.api_key or "",
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.settings.model,
                    "max_tokens": 800,
                    "temperature": self.settings.temperature,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
        content = "".join(
            block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
        )
        return parse_json_object(content)
