"""Клиент к LLM (Ollama)."""

from .client import (
    NO_ANSWER_MESSAGE,
    SYSTEM_INSTRUCTION,
    OllamaClient,
    OllamaError,
    get_llm_client,
)

__all__ = [
    "NO_ANSWER_MESSAGE",
    "SYSTEM_INSTRUCTION",
    "OllamaClient",
    "OllamaError",
    "get_llm_client",
]
