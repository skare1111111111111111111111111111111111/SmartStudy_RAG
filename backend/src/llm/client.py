from __future__ import annotations

import time
from typing import Any

import requests

from src.config import (
    HEALTH_CACHE_SECONDS,
    LLM_MAX_CONTEXT_CHARS,
    LLM_NUM_PREDICT,
    LLM_TEMPERATURE,
    OLLAMA_MODEL,
    OLLAMA_NUM_CTX,
    OLLAMA_NUM_THREAD,
    OLLAMA_TIMEOUT,
    OLLAMA_URL,
)

SYSTEM_INSTRUCTION = (
    "Ты — ассистент студента.\n"
    "Отвечай строго по предоставленному КОНТЕКСТУ, не используй знания вне контекста.\n"
    "Если в контексте недостаточно данных, напиши: «В загруженных документах ответ не найден».\n"
    "Требования к ответу:\n"
    "1) Начни с короткого вывода в 1-2 предложениях.\n"
    "2) Затем дай разверненное объяснение (2-5 пунктов или абзацев).\n"
    "3) Для ключевых фактов добавляй ссылки на источник в формате [source, стр. N].\n"
    "4) Не выдумывай факты и не противоречь контексту."
)
NO_ANSWER_MESSAGE = "В загруженных документах ответ не найден."


def _sanitize_answer_language(answer_language: str | None) -> str | None:
    if answer_language is None:
        return None

    cleaned = "".join(
        char for char in answer_language.strip() if char.isalnum() or char in {"-", "_", " "}
    ).strip()
    if not cleaned:
        return None
    return cleaned[:32]


class OllamaError(Exception):
    """Ошибка при обращении к Ollama."""


class OllamaClient:
    """Клиент к локальной LLM через Ollama."""

    def __init__(
        self,
        base_url: str = OLLAMA_URL,
        model: str = OLLAMA_MODEL,
        temperature: float = LLM_TEMPERATURE,
        num_predict: int = LLM_NUM_PREDICT,
        timeout: float = OLLAMA_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.num_predict = num_predict
        self.timeout = timeout
        self._availability_cache: tuple[bool, float] | None = None

    def build_context(
        self,
        chunks: list[dict[str, Any]],
        max_chars: int = LLM_MAX_CONTEXT_CHARS,
    ) -> str:
        """Склеивает найденные чанки в текст для промпта (с лимитом длины)."""
        parts: list[str] = []
        total = 0

        for chunk in chunks:
            text = chunk.get("text", "").strip()
            if not text:
                continue

            source = chunk.get("source", "unknown")
            page = chunk.get("page")
            if page is not None:
                header = f"[{source}, стр. {page}]"
            else:
                header = f"[{source}]"

            block = f"{header}\n{text}"
            if total + len(block) > max_chars:
                remaining = max_chars - total
                if remaining > 120:
                    parts.append(f"{header}\n{text[: remaining - len(header) - 4]}...")
                break

            parts.append(block)
            total += len(block) + 2

        return "\n\n".join(parts)

    def build_prompt(
        self,
        question: str,
        context: str,
        answer_language: str | None = None,
    ) -> str:
        language = _sanitize_answer_language(answer_language)
        language_instruction = ""
        if language:
            language_instruction = (
                f"\nЯЗЫК ОТВЕТА: {language}.\n"
                "Отвечай только на этом языке."
            )

        return (
            f"{SYSTEM_INSTRUCTION}{language_instruction}\n\n"
            f"КОНТЕКСТ:\n{context}\n\n"
            f"ВОПРОС: {question.strip()}\n\n"
            "ОТВЕТ:"
        )

    def generate(self, prompt: str) -> str:
        """Отправляет промпт в Ollama и возвращает текст ответа."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.num_predict,
                "num_ctx": OLLAMA_NUM_CTX,
                "num_thread": OLLAMA_NUM_THREAD,
            },
        }

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except requests.ConnectionError as exc:
            raise OllamaError(
                f"Не удалось подключиться к Ollama ({self.base_url}). "
                "Убедитесь, что Ollama запущена."
            ) from exc
        except requests.HTTPError as exc:
            raise OllamaError(
                f"Ollama вернула ошибку {response.status_code}: {response.text}"
            ) from exc
        except requests.RequestException as exc:
            raise OllamaError(f"Ошибка запроса к Ollama: {exc}") from exc

        data = response.json()
        answer = data.get("response", "").strip()
        if not answer:
            raise OllamaError("Ollama вернула пустой ответ.")
        return answer

    def answer(
        self,
        question: str,
        chunks: list[dict[str, Any]],
        answer_language: str | None = None,
    ) -> str:
        """Формирует промпт из чанков и генерирует ответ."""
        if not question or not question.strip():
            raise ValueError("Вопрос не может быть пустым")

        context = self.build_context(chunks)
        if not context.strip():
            return NO_ANSWER_MESSAGE

        prompt = self.build_prompt(
            question,
            context,
            answer_language=answer_language,
        )
        return self.generate(prompt)

    def is_available(self) -> bool:
        """Проверяет, доступна ли Ollama (с кэшем)."""
        now = time.monotonic()
        if self._availability_cache is not None:
            cached, ts = self._availability_cache
            if now - ts < HEALTH_CACHE_SECONDS:
                return cached

        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5.0,
            )
            available = response.status_code == 200
        except requests.RequestException:
            available = False

        self._availability_cache = (available, now)
        return available


_client: OllamaClient | None = None


def get_llm_client(
    base_url: str = OLLAMA_URL,
    model: str = OLLAMA_MODEL,
) -> OllamaClient:
    """Возвращает один экземпляр LLM-клиента на всё приложение."""
    global _client
    if _client is None:
        _client = OllamaClient(base_url=base_url, model=model)
    return _client
