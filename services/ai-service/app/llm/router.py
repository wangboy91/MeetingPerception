from typing import Any

from app.core.config import llm_settings
from app.llm.anthropic import AnthropicProvider
from app.llm.base import LlmProvider
from app.llm.mock_provider import MockLlmProvider
from app.llm.openai_compatible import OpenAICompatibleProvider


class LlmRouter:
    def __init__(self) -> None:
        self.settings = llm_settings()
        self.mock = MockLlmProvider()
        self.provider = self._create_provider()

    def _create_provider(self) -> LlmProvider:
        if not self.settings.cloud_enabled:
            return self.mock
        if self.settings.provider == "anthropic":
            return AnthropicProvider(self.settings)
        if self.settings.provider == "openai-compatible":
            return OpenAICompatibleProvider(self.settings)
        return self.mock

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        self.settings = llm_settings()
        self.provider = self._create_provider()
        try:
            return await self.provider.complete_json(system_prompt, user_prompt, schema)
        except Exception:
            return await self.mock.complete_json(system_prompt, user_prompt, schema)
