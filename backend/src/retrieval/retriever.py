from __future__ import annotations

from typing import Any

from chromadb.api.models.Collection import Collection

from src.config import CHROMA_PATH, TOP_K
from src.retrieval.chroma_store import COLLECTION_NAME, get_collection
from src.retrieval.embedding import Embedder, get_embedder


class Retriever:
    """Обёртка над Chroma: ищет чанки, похожие на вопрос пользователя."""

    def __init__(
        self,
        chroma_path: str = CHROMA_PATH,
        collection_name: str = COLLECTION_NAME,
        embedder: Embedder | None = None,
    ) -> None:
        self.chroma_path = chroma_path
        self.collection_name = collection_name
        self._embedder = embedder
        self._collection: Collection | None = None

    @property
    def embedder(self) -> Embedder:
        if self._embedder is None:
            self._embedder = get_embedder()
        return self._embedder

    @property
    def collection(self) -> Collection:
        if self._collection is None:
            self._collection = get_collection(self.chroma_path, self.collection_name)
        return self._collection

    def search(
        self,
        question: str,
        top_k: int = TOP_K,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Вопрос → список чанков: text, source, page, distance."""
        if not question or not question.strip():
            raise ValueError("Вопрос не может быть пустым")

        query_kwargs: dict[str, Any] = {
            "query_embeddings": [self.embedder.encode(question)],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_kwargs["where"] = where

        raw = self.collection.query(**query_kwargs)
        return self._format_results(raw)

    def count(self) -> int:
        """Сколько чанков сейчас в коллекции."""
        return self.collection.count()

    @staticmethod
    def _format_results(raw: dict[str, Any]) -> list[dict[str, Any]]:
        documents = raw.get("documents") or [[]]
        metadatas = raw.get("metadatas") or [[]]
        distances = raw.get("distances") or [[]]

        if not documents or not documents[0]:
            return []

        formatted: list[dict[str, Any]] = []
        for text, metadata, distance in zip(
            documents[0],
            metadatas[0],
            distances[0],
            strict=True,
        ):
            metadata = metadata or {}
            formatted.append(
                {
                    "text": text,
                    "source": metadata.get("source", "unknown"),
                    "page": metadata.get("page"),
                    "distance": distance,
                }
            )
        return formatted


_retriever: Retriever | None = None


def get_retriever(
    chroma_path: str = CHROMA_PATH,
    collection_name: str = COLLECTION_NAME,
) -> Retriever:
    """Возвращает один экземпляр ретривера на всё приложение."""
    global _retriever
    if _retriever is None:
        _retriever = Retriever(
            chroma_path=chroma_path,
            collection_name=collection_name,
        )
    return _retriever
