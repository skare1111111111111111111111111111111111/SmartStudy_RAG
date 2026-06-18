"""Пакет поиска: эмбеддинги и ретривер по Chroma."""

from src.retrieval.embedding import (
    DEFAULT_MODEL,
    VECTOR_SIZE,
    Embedder,
    get_embedder,
)
from src.retrieval.retriever import (
    COLLECTION_NAME,
    Retriever,
    get_retriever,
)

__all__ = [
    "COLLECTION_NAME",
    "DEFAULT_MODEL",
    "Embedder",
    "Retriever",
    "VECTOR_SIZE",
    "get_embedder",
    "get_retriever",
]
