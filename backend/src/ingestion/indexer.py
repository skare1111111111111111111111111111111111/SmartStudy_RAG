from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from src.config import CHROMA_PATH, CHUNK_OVERLAP, CHUNK_SIZE, DOCUMENTS_PATH
from src.ingestion.chunker import chunk_pages
from src.ingestion.parser import SUPPORTED_EXTENSIONS, parse_file
from src.retrieval.embedding import Embedder, get_embedder
from src.retrieval.retriever import COLLECTION_NAME


class Indexer:
    """Записывает чанки с эмбеддингами в Chroma для последующего поиска."""

    def __init__(
        self,
        chroma_path: str = CHROMA_PATH,
        collection_name: str = COLLECTION_NAME,
        embedder: Embedder | None = None,
    ) -> None:
        self.chroma_path = chroma_path
        self.collection_name = collection_name
        self._embedder = embedder
        self._client: chromadb.ClientAPI | None = None
        self._collection: Collection | None = None

    @property
    def embedder(self) -> Embedder:
        if self._embedder is None:
            self._embedder = get_embedder()
        return self._embedder

    @property
    def client(self) -> chromadb.ClientAPI:
        if self._client is None:
            self._client = chromadb.PersistentClient(path=self.chroma_path)
        return self._client

    @property
    def collection(self) -> Collection:
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
            )
        return self._collection

    def add_chunks(self, chunks: list[dict[str, Any]]) -> int:
        """Добавляет чанки в Chroma. Возвращает количество добавленных записей."""
        if not chunks:
            return 0

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for chunk in chunks:
            ids.append(f"{chunk['source']}_{chunk['page']}_{chunk['chunk_id']}")
            documents.append(chunk["text"])
            metadatas.append(
                {
                    "source": chunk["source"],
                    "page": chunk["page"],
                    "chunk_id": chunk["chunk_id"],
                }
            )

        embeddings = self.embedder.encode_batch(documents)
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(chunks)

    def delete_by_source(self, source: str) -> None:
        """Удаляет все чанки одного файла перед переиндексацией."""
        if self.collection.count() == 0:
            return

        self.collection.delete(where={"source": source})

    def index_file(
        self,
        file_path: str | Path,
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP,
    ) -> int:
        """Полный пайплайн: файл → страницы → чанки → Chroma."""
        path = Path(file_path)
        pages = parse_file(path)
        if not pages:
            self.delete_by_source(path.name)
            return 0

        self.delete_by_source(path.name)
        chunks = chunk_pages(pages, chunk_size=chunk_size, overlap=overlap)
        return self.add_chunks(chunks)

    def index_directory(
        self,
        directory: str | Path | None = None,
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP,
    ) -> int:
        """Индексирует все поддерживаемые файлы в папке documents/."""
        dir_path = Path(directory or DOCUMENTS_PATH)
        if not dir_path.exists():
            raise FileNotFoundError(f"Папка не найдена: {dir_path}")

        total = 0
        for ext in sorted(SUPPORTED_EXTENSIONS):
            for file_path in sorted(dir_path.glob(f"*{ext}")):
                total += self.index_file(file_path, chunk_size, overlap)
        return total

    def count(self) -> int:
        return self.collection.count()


_indexer: Indexer | None = None


def get_indexer(
    chroma_path: str = CHROMA_PATH,
    collection_name: str = COLLECTION_NAME,
) -> Indexer:
    global _indexer
    if _indexer is None:
        _indexer = Indexer(chroma_path=chroma_path, collection_name=collection_name)
    return _indexer


def index_file(file_path: str | Path, **kwargs: Any) -> int:
    """Индексирует один файл (удобная обёртка для пайплайна)."""
    return get_indexer().index_file(file_path, **kwargs)


def index_directory(directory: str | Path | None = None, **kwargs: Any) -> int:
    """Индексирует все документы в папке (удобная обёртка для пайплайна)."""
    return get_indexer().index_directory(directory, **kwargs)
