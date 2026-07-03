from abc import ABC, abstractmethod
from typing import Any


class LlmProvider(ABC):
    @abstractmethod
    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        pass
