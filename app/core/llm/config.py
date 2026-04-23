from __future__ import annotations

import os
from dataclasses import dataclass

from app.core.llm.prompt_registry import BINARY_FEATURE_AI_PROMPT_VERSION


def _env(name: str) -> str | None:
    value = (os.getenv(name) or "").strip()
    return value or None


def _int_env(name: str, *, default: int, minimum: int = 0) -> int:
    raw = _env(name)
    if raw is None:
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


def _bool_env(name: str, *, default: bool) -> bool:
    raw = _env(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class LlmConfig:
    provider_name: str
    base_url: str | None
    api_key: str | None
    model_name: str
    timeout_seconds: int
    retry_count: int
    prompt_version: str
    cache_enabled: bool
    top_row_cap: int

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.model_name)


def get_llm_config() -> LlmConfig:
    return LlmConfig(
        provider_name="openai_compatible",
        base_url=_env("INSIGHT_HUB_LLM_BASE_URL"),
        api_key=_env("INSIGHT_HUB_LLM_API_KEY"),
        model_name=_env("INSIGHT_HUB_LLM_MODEL") or "",
        timeout_seconds=_int_env(
            "INSIGHT_HUB_LLM_TIMEOUT_SECONDS",
            default=20,
            minimum=1,
        ),
        retry_count=_int_env(
            "INSIGHT_HUB_LLM_MAX_RETRIES",
            default=1,
            minimum=0,
        ),
        prompt_version=BINARY_FEATURE_AI_PROMPT_VERSION,
        cache_enabled=_bool_env("INSIGHT_HUB_LLM_ENABLE_CACHE", default=True),
        top_row_cap=20,
    )
