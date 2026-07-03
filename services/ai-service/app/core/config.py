import os
from dataclasses import dataclass
from typing import Literal

LlmProviderName = Literal["mock", "openai-compatible", "anthropic"]


@dataclass(frozen=True)
class LlmSettings:
    provider: LlmProviderName
    base_url: str
    model: str
    api_key: str | None
    cloud_allowed: bool
    timeout_seconds: float
    temperature: float

    @property
    def cloud_enabled(self) -> bool:
        return self.cloud_allowed and self.provider != "mock" and bool(
            self.api_key and self.base_url and self.model
        )


def llm_settings() -> LlmSettings:
    provider = os.getenv("MEETING_COPILOT_LLM_PROVIDER", "mock").strip() or "mock"
    if provider not in {"mock", "openai-compatible", "anthropic"}:
        provider = "mock"

    base_url = os.getenv("MEETING_COPILOT_LLM_BASE_URL", "").strip()
    if not base_url and provider == "openai-compatible":
        base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    if not base_url and provider == "anthropic":
        base_url = os.getenv("ANTHROPIC_BASE_URL", "").strip()

    model = os.getenv("MEETING_COPILOT_LLM_MODEL", os.getenv("MODEL", "mock")).strip()
    stored = _stored_llm_settings()
    provider = str(stored.get("llmProvider", provider)).strip() or provider
    if provider not in {"mock", "openai-compatible", "anthropic"}:
        provider = "mock"
    base_url = str(stored.get("llmBaseUrl", base_url)).strip().rstrip("/")
    model = str(stored.get("llmModel", model)).strip() or model

    return LlmSettings(
        provider=provider,  # type: ignore[arg-type]
        base_url=base_url.rstrip("/"),
        model=model,
        api_key=os.getenv("MEETING_COPILOT_LLM_API_KEY"),
        cloud_allowed=bool(stored.get("cloudLlmEnabled", provider != "mock")),
        timeout_seconds=float(os.getenv("MEETING_COPILOT_LLM_TIMEOUT_SECONDS", "8")),
        temperature=float(os.getenv("MEETING_COPILOT_LLM_TEMPERATURE", "0.2")),
    )


def _stored_llm_settings() -> dict[str, object]:
    try:
        from app.storage.repositories import SettingsRepository

        return SettingsRepository().get("app") or {}
    except Exception:
        return {}
