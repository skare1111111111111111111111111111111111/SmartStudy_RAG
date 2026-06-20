"""Сервисный слой API: обёртки над src-модулями."""

from src.llm import OllamaClient as LLMClient, OllamaError, get_llm_client as get_llm
from src.api.services.rag import ask

__all__ = ["LLMClient", "OllamaError", "ask", "get_llm"]
