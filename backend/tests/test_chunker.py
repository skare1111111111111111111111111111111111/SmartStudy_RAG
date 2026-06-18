from __future__ import annotations

import pytest

from ingestion.chunker import chunk_pages, chunk_text


def test_chunk_text_empty_returns_empty_list() -> None:
    assert chunk_text("") == []
    assert chunk_text("   \n  ") == []


def test_chunk_text_overlap_must_be_less_than_size() -> None:
    with pytest.raises(ValueError, match="overlap"):
        chunk_text("текст", chunk_size=100, overlap=100)


def test_chunk_text_groups_small_paragraphs() -> None:
    text = (
        "Первый небольшой абзац.\n\n"
        "Второй небольшой абзац.\n\n"
        "Третий небольшой абзац.\n\n"
        "Четвёртый небольшой абзац."
    )
    chunks = chunk_text(text, chunk_size=50, overlap=10)

    assert len(chunks) >= 2
    joined = " ".join(c["text"] for c in chunks)
    assert "Первый" in joined
    assert "Четвёртый" in joined


def test_chunk_text_has_overlap_between_chunks() -> None:
    text = "Слово " * 80
    chunks = chunk_text(text, chunk_size=100, overlap=25)

    assert len(chunks) >= 2
    tail = chunks[0]["text"][-25:]
    assert tail in chunks[1]["text"]


def test_chunk_text_splits_long_paragraph() -> None:
    paragraph = "X" * 300
    chunks = chunk_text(paragraph, chunk_size=100, overlap=10)

    assert len(chunks) >= 3
    assert all(len(c["text"]) <= 100 for c in chunks)


def test_chunk_pages_adds_metadata() -> None:
    pages = [
        {"page": 1, "text": "Первый абзац.\n\nВторой абзац.", "source": "lecture.pdf"},
        {"page": 2, "text": "Текст второй страницы.", "source": "lecture.pdf"},
    ]
    chunks = chunk_pages(pages, chunk_size=50, overlap=10)

    assert len(chunks) >= 2
    assert all(c["source"] == "lecture.pdf" for c in chunks)
    assert any(c["page"] == 1 for c in chunks)
    assert any(c["page"] == 2 for c in chunks)

    page1_ids = [c["chunk_id"] for c in chunks if c["page"] == 1]
    page2_ids = [c["chunk_id"] for c in chunks if c["page"] == 2]
    assert page1_ids == list(range(len(page1_ids)))
    assert page2_ids == list(range(len(page2_ids)))


def test_chunk_pages_integration_with_sample_txt() -> None:
    from ingestion.parser import parse_file
    from pathlib import Path

    sample = Path(__file__).resolve().parents[1] / "ingestion" / "documents" / "sample.txt"
    pages = parse_file(sample)
    chunks = chunk_pages(pages, chunk_size=200, overlap=30)

    assert len(pages) == 1
    assert len(chunks) >= 2
    assert chunks[0]["source"] == "sample.txt"
    assert "машинное обучение" in chunks[0]["text"].lower()
