"""Чанкер: разбивает страницы на кусочки текста фиксированного размера."""

from __future__ import annotations

import re
from typing import Any


def chunk_pages(
    pages: list[dict[str, Any]],
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict[str, Any]]:
    """
    Разбивает список страниц на чанки.

    Формат выхода:
        [{
            "text": "...",
            "source": "lecture.pdf",
            "page": 1,
            "chunk_id": 0,
            "start_char": 0,
            "end_char": 120,
        }, ...]
    """
    all_chunks: list[dict[str, Any]] = []

    for page in pages:
        page_chunks = chunk_text(page["text"], chunk_size, overlap)
        for chunk in page_chunks:
            chunk["source"] = page["source"]
            chunk["page"] = page["page"]
        all_chunks.extend(page_chunks)

    return all_chunks


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict[str, Any]]:
    """
    Разбивает текст одной страницы на чанки.

    Алгоритм:
    1. Сначала группируем абзацы (разделитель \\n\\n), пока не наберётся ~chunk_size.
    2. Если один абзац длиннее chunk_size — режем посимвольно.
    3. Между чанками добавляем overlap (последние N символов предыдущего чанка).
    """
    text = text.strip()
    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError("overlap должен быть меньше chunk_size")

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return _chunk_by_chars(text, chunk_size, overlap)

    chunks: list[dict[str, Any]] = []
    current = ""
    chunk_id = 0
    overlap_prefix = ""

    def flush(content: str) -> None:
        nonlocal chunk_id, overlap_prefix, current
        content = content.strip()
        if not content:
            return

        start = text.find(content[: min(len(content), 80)])
        if start == -1:
            start = 0
        end = start + len(content)

        chunks.append(
            {
                "text": content,
                "start_char": start,
                "end_char": end,
                "chunk_id": chunk_id,
            }
        )
        chunk_id += 1
        overlap_prefix = content[-overlap:] if overlap > 0 else ""
        current = ""

    for para in paragraphs:
        if overlap_prefix:
            candidate = f"{overlap_prefix}\n\n{para}".strip()
        elif current:
            candidate = f"{current}\n\n{para}".strip()
        else:
            candidate = para

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            flush(current)
            candidate = f"{overlap_prefix}\n\n{para}".strip() if overlap_prefix else para

        if len(para) > chunk_size:
            if candidate and candidate != para:
                flush(candidate)

            char_chunks = _chunk_by_chars(para, chunk_size, overlap, start_chunk_id=chunk_id)
            if char_chunks:
                chunks.extend(char_chunks)
                chunk_id = char_chunks[-1]["chunk_id"] + 1
                overlap_prefix = char_chunks[-1]["text"][-overlap:] if overlap > 0 else ""
            current = ""
            continue

        current = candidate
        overlap_prefix = ""

    if current:
        flush(current)

    return chunks


def _chunk_by_chars(
    text: str,
    chunk_size: int,
    overlap: int,
    start_chunk_id: int = 0,
) -> list[dict[str, Any]]:
    """Посимвольная разбивка с перекрытием (для длинных абзацев)."""
    chunks: list[dict[str, Any]] = []
    start = 0
    chunk_id = start_chunk_id
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        if end < text_len:
            boundary = text.rfind("\n\n", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary
            else:
                space = text.rfind(" ", start, end)
                if space > start + chunk_size // 2:
                    end = space

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(
                {
                    "text": chunk,
                    "start_char": start,
                    "end_char": end,
                    "chunk_id": chunk_id,
                }
            )
            chunk_id += 1

        if end >= text_len:
            break

        start = max(end - overlap, start + 1)

    return chunks
