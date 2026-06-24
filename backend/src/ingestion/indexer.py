from __future__ import annotations

from pathlib import Path
from typing import Any

from chromadb.api.models.Collection import Collection

from src.config import (
    CHROMA_PATH,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DOCUMENTS_PATH,
    EMBEDDING_BATCH_SIZE,
)
from src.ingestion.chunker import chunk_pages
from src.ingestion.parser import SUPPORTED_EXTENSIONS, parse_file
from src.retrieval.chroma_store import COLLECTION_NAME, get_collection
from src.retrieval.embedding import Embedder, get_embedder


def _file_signature(path: Path) -> tuple[int, int]:
    stat = path.stat()
    return stat.st_mtime_ns, stat.st_size


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
        self._collection: Collection | None = None
        self._known_sources: set[str] | None = None

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

    def _invalidate_sources_cache(self) -> None:
        self._known_sources = None

    def _is_unchanged(self, source: str, signature: tuple[int, int]) -> bool:
        if self.collection.count() == 0:
            return False

        result = self.collection.get(
            where={"source": source},
            limit=1,
            include=["metadatas"],
        )
        metadatas = result.get("metadatas") or []
        if not metadatas or not metadatas[0]:
            return False

        meta = metadatas[0]
        return (
            meta.get("file_mtime_ns") == signature[0]
            and meta.get("file_size") == signature[1]
        )

    def add_chunks(
        self,
        chunks: list[dict[str, Any]],
        *,
        file_mtime_ns: int | None = None,
        file_size: int | None = None,
    ) -> int:
        """Добавляет чанки в Chroma. Возвращает количество добавленных записей."""
        if not chunks:
            return 0

        total = 0
        batch_size = EMBEDDING_BATCH_SIZE

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            ids: list[str] = []
            documents: list[str] = []
            metadatas: list[dict[str, Any]] = []

            for chunk in batch:
                ids.append(f"{chunk['source']}_{chunk['page']}_{chunk['chunk_id']}")
                documents.append(chunk["text"])
                metadata: dict[str, Any] = {
                    "source": chunk["source"],
                    "page": chunk["page"],
                    "chunk_id": chunk["chunk_id"],
                }
                if file_mtime_ns is not None:
                    metadata["file_mtime_ns"] = file_mtime_ns
                if file_size is not None:
                    metadata["file_size"] = file_size
                metadatas.append(metadata)

            embeddings = self.embedder.encode_batch(documents)
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            total += len(batch)

        self._invalidate_sources_cache()
        return total

    def delete_by_source(self, source: str) -> None:
        """Удаляет все чанки одного файла перед переиндексацией."""
        if self.collection.count() == 0:
            return

        self.collection.delete(where={"source": source})
        self._invalidate_sources_cache()

    def list_sources(self) -> list[str]:
        """Список проиндексированных файлов без полного скана метаданных."""
        if self._known_sources is not None:
            return sorted(self._known_sources)

        if self.collection.count() == 0:
            self._known_sources = set()
            return []

        data = self.collection.get(include=["metadatas"])
        sources: set[str] = set()
        for metadata in data.get("metadatas") or []:
            if metadata and metadata.get("source"):
                sources.add(metadata["source"])

        self._known_sources = sources
        return sorted(sources)

    def index_file(
        self,
        file_path: str | Path,
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP,
        *,
        force: bool = False,
    ) -> int:
        """Полный пайплайн: файл → страницы → чанки → Chroma."""
        path = Path(file_path)
        if not path.exists():
            self.delete_by_source(path.name)
            return 0

        signature = _file_signature(path)
        if not force and self._is_unchanged(path.name, signature):
            return 0

        pages = parse_file(path)
        if not pages:
            self.delete_by_source(path.name)
            return 0

        self.delete_by_source(path.name)
        chunks = chunk_pages(pages, chunk_size=chunk_size, overlap=overlap)
        return self.add_chunks(
            chunks,
            file_mtime_ns=signature[0],
            file_size=signature[1],
        )

    def index_directory(
        self,
        directory: str | Path | None = None,
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP,
        *,
        force: bool = False,
    ) -> int:
        """Индексирует все поддерживаемые файлы в папке documents/."""
        dir_path = Path(directory or DOCUMENTS_PATH)
        if not dir_path.exists():
            raise FileNotFoundError(f"Папка не найдена: {dir_path}")

        files: list[Path] = []
        for ext in sorted(SUPPORTED_EXTENSIONS):
            files.extend(sorted(dir_path.glob(f"*{ext}")))

        if force:
            actual_sources = {file_path.name for file_path in files}
            for source in self.list_sources():
                if source not in actual_sources:
                    self.delete_by_source(source)

        total = 0
        for file_path in files:
            total += self.index_file(file_path, chunk_size, overlap, force=force)
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
