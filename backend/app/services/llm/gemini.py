"""
Google Gemini LLM provider for text-to-SQL generation.
"""
from __future__ import annotations

import re

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.services.llm.base import LLMProvider


_SQL_FENCE_RE = re.compile(r"```(?:sql)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def _extract_sql(text: str) -> str:
    """Strip markdown fences if the model wrapped its answer in them."""
    m = _SQL_FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        genai.configure(api_key=api_key)
        self._model_name = model
        self._gen_cfg = GenerationConfig(temperature=0.05, max_output_tokens=1024)

    async def generate_sql(
        self,
        system_prompt: str,
        conversation: list[dict[str, str]],
        user_message: str,
    ) -> str:
        model = genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system_prompt,
            generation_config=self._gen_cfg,
        )

        # Build Gemini history (prior turns only, not the current message)
        history = []
        for turn in conversation:
            role = "model" if turn["role"] == "assistant" else "user"
            history.append({"role": role, "parts": [turn["content"]]})

        chat = model.start_chat(history=history)
        response = await chat.send_message_async(user_message)
        return _extract_sql(response.text)
