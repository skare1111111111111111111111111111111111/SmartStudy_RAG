from __future__ import annotations

import httpx

from config import LLM_NUM_PREDICT, LLM_TEMPERATURE, OLLAMA_MODEL, OLLAMA_URL


class LLMClient:
    """HTTP-клиент для Ollama (локальная LLM)."""

    def __init__(
        self,
        base_url: str = OLLAMA_URL,
        model: str = OLLAMA_MODEL,
        temperature: float = LLM_TEMPERATURE,
        num_predict: int = LLM_NUM_PREDICT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.num_predict = num_predict

    def generate(self, prompt: str) -> str:
        if not prompt.strip():
            raise ValueError("Промпт не может быть пустым")

        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.num_predict,
                },
            },
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["response"]

    def is_available(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except httpx.HTTPError:
            return False


_llm: LLMClient | None = None


def get_llm() -> LLMClient:
    global _llm
    if _llm is None:
        _llm = LLMClient()
    return _llm
