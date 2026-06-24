from __future__ import annotations

from pathlib import Path
from typing import Sequence

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.ingestion.indexer import Indexer, get_indexer
from src.llm.client import get_llm_client
from src.retrieval.retriever import Retriever, get_retriever
from src.api.routes.stats import invalidate_stats_cache


class MockEmbedder:
    vector_size = 384

    @staticmethod
    def _vector(text: str) -> list[float]:
        seed = sum(ord(char) for char in text) % 997
        return [((seed + index) % 997) / 997.0 for index in range(384)]

    def encode(self, text: str) -> list[float]:
        return self._vector(text)

    def encode_batch(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]


class MockLLM:
    def answer(self, question: str, chunks: list) -> str:
        return "Машинное обучение — подмножество искусственного интеллекта."

    def is_available(self) -> bool:
        return True


@pytest.fixture
def api_client(chroma_dir: str) -> TestClient:
    embedder = MockEmbedder()
    indexer = Indexer(chroma_path=chroma_dir, embedder=embedder)
    retriever = Retriever(chroma_path=chroma_dir, embedder=embedder)
    llm = MockLLM()

    app.dependency_overrides[get_indexer] = lambda: indexer
    app.dependency_overrides[get_retriever] = lambda: retriever
    app.dependency_overrides[get_llm_client] = lambda: llm

    invalidate_stats_cache()

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    invalidate_stats_cache()


@pytest.fixture
def chroma_dir(tmp_path: Path) -> str:
    return str(tmp_path / "chroma")


def test_health(api_client: TestClient) -> None:
    response = api_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["ollama"] == "available"


def test_stats_empty(api_client: TestClient) -> None:
    response = api_client.get("/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["chunks_count"] == 0
    assert data["documents"] == []


def test_reindex_and_stats(api_client: TestClient, tmp_path: Path) -> None:
    doc = tmp_path / "lecture.txt"
    doc.write_text(
        "Машинное обучение позволяет учиться на данных.\n\n"
        "Нейронные сети — основа deep learning.",
        encoding="utf-8",
    )

    reindex = api_client.post("/reindex", json={"path": str(doc)})
    assert reindex.status_code == 200
    assert reindex.json()["chunks_added"] >= 1

    stats = api_client.get("/stats")
    assert stats.status_code == 200
    assert stats.json()["chunks_count"] >= 1
    assert "lecture.txt" in stats.json()["documents"]


def test_ask_empty_database(api_client: TestClient) -> None:
    response = api_client.post("/ask", json={"question": "Что такое ML?"})

    assert response.status_code == 200
    data = response.json()
    assert "не найден" in data["answer"].lower()
    assert data["sources"] == []


def test_ask_with_indexed_document(api_client: TestClient, tmp_path: Path) -> None:
    doc = tmp_path / "notes.txt"
    doc.write_text(
        "Машинное обучение — подмножество искусственного интеллекта.",
        encoding="utf-8",
    )
    api_client.post("/reindex", json={"path": str(doc)})

    response = api_client.post(
        "/ask",
        json={"question": "Что такое машинное обучение?", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"]
    assert len(data["sources"]) >= 1
    assert data["sources"][0]["source"] == "notes.txt"


def test_ask_validation_error(api_client: TestClient) -> None:
    response = api_client.post("/ask", json={"question": ""})

    assert response.status_code == 422


def test_reindex_missing_path(api_client: TestClient) -> None:
    response = api_client.post("/reindex", json={"path": "/no/such/path"})

    assert response.status_code == 404
