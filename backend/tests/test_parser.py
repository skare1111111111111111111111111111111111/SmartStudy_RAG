from __future__ import annotations

from pathlib import Path

import pytest

from ingestion.parser import SUPPORTED_EXTENSIONS, parse_file


def test_parse_txt_returns_page_with_source(sample_txt: Path) -> None:
    pages = parse_file(sample_txt)

    assert len(pages) == 1
    assert pages[0]["page"] == 1
    assert pages[0]["source"] == "lecture.txt"
    assert "Машинное обучение" in pages[0]["text"]
    assert "Нейронные сети" in pages[0]["text"]


def test_parse_empty_txt_returns_empty_list(empty_txt: Path) -> None:
    assert parse_file(empty_txt) == []


def test_parse_docx_joins_paragraphs(sample_docx: Path) -> None:
    pages = parse_file(sample_docx)

    assert len(pages) == 1
    assert pages[0]["page"] == 1
    assert pages[0]["source"] == "notes.docx"
    assert "Первый абзац лекции." in pages[0]["text"]
    assert "Второй абзац про нейросети." in pages[0]["text"]
    assert "\n\n" in pages[0]["text"]


def test_parse_pdf_extracts_pages(sample_pdf: Path) -> None:
    pages = parse_file(sample_pdf)

    assert len(pages) >= 1
    assert pages[0]["source"] == "sample.pdf"
    assert pages[0]["page"] == 1
    assert "konveyernyy registr" in pages[0]["text"].lower()


def test_parse_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError, match="не найден"):
        parse_file("no_such_file.txt")


def test_parse_unsupported_format_raises(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_text("a,b,c", encoding="utf-8")

    with pytest.raises(ValueError, match="Неподдерживаемый формат"):
        parse_file(path)


def test_supported_extensions() -> None:
    assert SUPPORTED_EXTENSIONS == {".pdf", ".docx", ".txt"}
