"""
Abstract base class for LLM providers.

Any provider (Gemini, OpenAI, Anthropic, …) must implement this interface
so the chat service remains decoupled from the underlying model.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Minimal interface for text-to-SQL LLM backends."""

    @abstractmethod
    async def generate_sql(
        self,
        system_prompt: str,
        conversation: list[dict[str, str]],
        user_message: str,
    ) -> str:
        """
        Generate a SQL SELECT statement from natural language.

        Args:
            system_prompt: Static system context (schema description, rules).
            conversation:  Prior turns as [{"role": "user"|"assistant", "content": "..."}].
            user_message:  The current user question.

        Returns:
            A SQL string (SELECT only).
        """
