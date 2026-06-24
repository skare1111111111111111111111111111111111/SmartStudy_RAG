from __future__ import annotations

import functools
from typing import Sequence

from sentence_transformers import SentenceTransformer

from src.config import EMBEDDING_BATCH_SIZE, EMBEDDING_MODEL

DEFAULT_MODEL = EMBEDDING_MODEL
VECTOR_SIZE = 384


def _normalize_query(text: str) -> str:
    return " ".join(text.split())


class Embedder:
    """Превращает текст в векторы для векторного поиска в Chroma."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        batch_size: int = EMBEDDING_BATCH_SIZE,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    @property
    def vector_size(self) -> int:
        return self.model.get_sentence_embedding_dimension()

    @functools.lru_cache(maxsize=128)
    def _encode_cached(self, text: str) -> tuple[float, ...]:
        vector = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return tuple(vector.tolist())

    def encode(self, text: str) -> list[float]:
        """Один текст → вектор из 384 чисел."""
        if not text or not text.strip():
            raise ValueError("Текст для эмбеддинга не может быть пустым")

        return list(self._encode_cached(_normalize_query(text)))

    def encode_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """Список текстов → список векторов (для индексации чанков)."""
        if not texts:
            return []

        cleaned = [text.strip() for text in texts]
        if any(not text for text in cleaned):
            raise ValueError("Все тексты для эмбеддинга должны быть непустыми")

        vectors = self.model.encode(
            list(cleaned),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=self.batch_size,
        )
        return vectors.tolist()


_embedder: Embedder | None = None


def get_embedder(model_name: str = DEFAULT_MODEL) -> Embedder:
    """Возвращает один экземпляр эмбеддера на всё приложение."""
    global _embedder
    if _embedder is None or _embedder.model_name != model_name:
        _embedder = Embedder(model_name=model_name)
    return _embedder
