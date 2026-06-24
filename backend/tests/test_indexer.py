from __future__ import annotations

from pathlib import Path
from typing import Sequence

import pytest

from ingestion.indexer import Indexer
from retrieval.retriever import Retriever


class MockEmbedder:
    """Быстрый эмбеддер для тестов без загрузки ML-модели."""

    vector_size = 384

    @staticmethod
    def _vector(text: str) -> list[float]:
        seed = sum(ord(char) for char in text) % 997
        return [((seed + index) % 997) / 997.0 for index in range(384)]

    def encode(self, text: str) -> list[float]:
        return self._vector(text)

    def encode_batch(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]


@pytest.fixture
def chroma_dir(tmp_path: Path) -> str:
    return str(tmp_path / "chroma")


@pytest.fixture
def indexer(chroma_dir: str) -> Indexer:
    return Indexer(chroma_path=chroma_dir, embedder=MockEmbedder())


@pytest.fixture
def retriever(chroma_dir: str) -> Retriever:
    return Retriever(chroma_path=chroma_dir, embedder=MockEmbedder())


def test_add_chunks_writes_to_chroma(indexer: Indexer) -> None:
    chunks = [
        {
            "text": "Машинное обучение — подмножество AI.",
            "source": "lecture.txt",
            "page": 1,
            "chunk_id": 0,
            "start_char": 0,
            "end_char": 36,
        }
    ]

    added = indexer.add_chunks(chunks)

    assert added == 1
    assert indexer.count() == 1


def test_index_file_full_pipeline(indexer: Indexer, tmp_path: Path) -> None:
    doc = tmp_path / "notes.txt"
    doc.write_text(
        "Нейронные сети состоят из слоёв.\n\n"
        "Каждый слой выполняет преобразование данных.",
        encoding="utf-8",
    )

    count = indexer.index_file(doc, chunk_size=80, overlap=10)

    assert count >= 1
    assert indexer.count() == count


def test_reindex_replaces_old_chunks(indexer: Indexer, tmp_path: Path) -> None:
    doc = tmp_path / "lecture.txt"
    doc.write_text("Старый текст про ML.", encoding="utf-8")
    indexer.index_file(doc, chunk_size=200, overlap=20)

    doc.write_text("Новый текст про нейросети и глубокое обучение.", encoding="utf-8")
    indexer.index_file(doc, chunk_size=200, overlap=20)

    stored = indexer.collection.get(include=["documents"])
    assert len(stored["ids"]) >= 1
    assert all("Новый текст" in text for text in stored["documents"])


def test_index_directory_indexes_supported_files(indexer: Indexer, tmp_path: Path) -> None:
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir()
    (docs_dir / "a.txt").write_text("Текст файла A.", encoding="utf-8")
    (docs_dir / "b.csv").write_text("ignored", encoding="utf-8")

    total = indexer.index_directory(docs_dir, chunk_size=200, overlap=20)

    assert total >= 1
    assert indexer.count() == total


def test_force_reindex_removes_deleted_sources(indexer: Indexer, tmp_path: Path) -> None:
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir()
    first = docs_dir / "first.txt"
    second = docs_dir / "second.txt"
    first.write_text("Данные по теме A.", encoding="utf-8")
    second.write_text("Данные по теме B.", encoding="utf-8")

    indexer.index_directory(docs_dir, chunk_size=200, overlap=20, force=True)
    assert set(indexer.list_sources()) == {"first.txt", "second.txt"}

    second.unlink()
    indexer.index_directory(docs_dir, chunk_size=200, overlap=20, force=True)

    assert set(indexer.list_sources()) == {"first.txt"}


def test_ingestion_to_retrieval_pipeline(
    indexer: Indexer,
    retriever: Retriever,
    tmp_path: Path,
) -> None:
    doc = tmp_path / "sample.txt"
    doc.write_text(
        "Машинное обучение позволяет компьютерам учиться на данных.\n\n"
        "Нейронные сети — основа глубокого обучения.",
        encoding="utf-8",
    )

    indexer.index_file(doc, chunk_size=100, overlap=15)
    results = retriever.search("машинное обучение", top_k=3)

    assert len(results) >= 1
    assert results[0]["source"] == "sample.txt"
    assert results[0]["page"] == 1
    assert "text" in results[0]
    assert "distance" in results[0]


def test_index_sample_document_from_repo(indexer: Indexer, retriever: Retriever) -> None:
    sample = Path(__file__).resolve().parents[1] / "src" / "ingestion" / "documents" / "sample.txt"

    count = indexer.index_file(sample, chunk_size=200, overlap=30)
    results = retriever.search("конвейерный регистр", top_k=2)

    assert count >= 2
    assert len(results) >= 1
    assert results[0]["source"] == "sample.txt"
