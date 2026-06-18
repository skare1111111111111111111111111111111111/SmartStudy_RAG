"""Парсер документов: PDF, DOCX, TXT → список страниц с текстом."""

from __future__ import annotations

from pathlib import Path
from typing import Any

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def parse_file(file_path: str | Path) -> list[dict[str, Any]]:
    """
    Читает файл и возвращает список страниц.

    Формат выхода:
        [{"page": 1, "text": "...", "source": "lecture.pdf"}, ...]
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Неподдерживаемый формат: {suffix}. "
            f"Поддерживаются: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    source = path.name

    if suffix == ".pdf":
        return _parse_pdf(path, source)
    if suffix == ".docx":
        return _parse_docx(path, source)
    return _parse_txt(path, source)


def _parse_pdf(path: Path, source: str) -> list[dict[str, Any]]:
    from pypdf import PdfReader

    reader = PdfReader(path)
    pages: list[dict[str, Any]] = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"page": i + 1, "text": text, "source": source})

    return pages


def _parse_docx(path: Path, source: str) -> list[dict[str, Any]]:
    from docx import Document

    document = Document(path)
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]

    if not paragraphs:
        return []

    # DOCX не даёт номера страниц без сложной логики — весь документ как одна «страница».
    return [{"page": 1, "text": "\n\n".join(paragraphs), "source": source}]


def _parse_txt(path: Path, source: str) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")

    if not text.strip():
        return []

    return [{"page": 1, "text": text, "source": source}]
