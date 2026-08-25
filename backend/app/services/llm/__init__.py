"""
LLM provider factory.

To swap providers, change LLM_PROVIDER env var or extend this factory.
"""
from __future__ import annotations

from app.config import get_settings
from app.services.llm.base import LLMProvider


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == "gemini":
        from app.services.llm.gemini import GeminiProvider
        return GeminiProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )
    # Future providers:
    # elif provider == "openai":
    #     from app.services.llm.openai import OpenAIProvider
    #     return OpenAIProvider(api_key=settings.openai_api_key)
    else:
        raise ValueError(f"Unknown LLM provider: {provider!r}. Set LLM_PROVIDER=gemini")
