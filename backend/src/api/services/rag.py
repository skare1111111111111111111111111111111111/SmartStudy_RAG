from __future__ import annotations

import re
from typing import Any

from src.config import LLM_TOP_K
from src.llm import NO_ANSWER_MESSAGE, OllamaClient, OllamaError
from src.retrieval import Retriever

_TOKEN_RE = re.compile(r"[A-Za-zА-Яа-я0-9]{3,}")
_MIN_QUESTION_OVERLAP = 0.2
_STOP_WORDS = {
    "это",
    "что",
    "чего",
    "такое",
    "как",
    "какой",
    "какие",
    "подробно",
    "объясни",
    "состоит",
    "для",
    "из",
    "или",
    "при",
    "про",
    "если",
    "the",
    "and",
    "for",
    "with",
    "from",
    "this",
}


def _tokenize(text: str) -> set[str]:
    tokens = {
        token
        for token in _TOKEN_RE.findall(text.lower())
        if token not in _STOP_WORDS
    }
    return tokens


def _rank_chunks_by_overlap(question: str, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    question_tokens = _tokenize(question)
    if not question_tokens:
        return chunks

    required_common_tokens = 2 if len(question_tokens) >= 4 else 1
    scored: list[tuple[float, float, dict[str, Any]]] = []
    for chunk in chunks:
        text = (chunk.get("text") or "").strip()
        if not text:
            continue
        chunk_tokens = _tokenize(text)
        if not chunk_tokens:
            continue

        common_tokens = len(question_tokens & chunk_tokens)
        if common_tokens < required_common_tokens:
            continue

        overlap = common_tokens / len(question_tokens)
        distance = chunk.get("distance")
        distance_rank = -float(distance) if isinstance(distance, (int, float)) else float("-inf")
        scored.append((overlap, distance_rank, chunk))

    if not scored:
        return []

    max_overlap = max(item[0] for item in scored)
    if max_overlap < _MIN_QUESTION_OVERLAP:
        return []

    overlap_cutoff = max(_MIN_QUESTION_OVERLAP, max_overlap * 0.45)
    filtered = [item for item in scored if item[0] >= overlap_cutoff]
    filtered.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[2] for item in filtered]


def _dedupe_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[Any, Any, str]] = set()

    for chunk in chunks:
        text = (chunk.get("text") or "").strip()
        if not text:
            continue

        key = (chunk.get("source"), chunk.get("page"), text[:140])
        if key in seen:
            continue

        seen.add(key)
        deduped.append(chunk)

    return deduped


def ask(
    question: str,
    retriever: Retriever,
    llm: OllamaClient,
    top_k: int = 5,
    answer_language: str | None = None,
) -> dict[str, Any]:
    """RAG-пайплайн: поиск чанков → ответ LLM."""
    chunks = retriever.search(question, top_k=top_k)

    if not chunks:
        return {"answer": NO_ANSWER_MESSAGE, "sources": []}

    llm_candidates = _dedupe_chunks(chunks)
    ranked_chunks = _rank_chunks_by_overlap(question, llm_candidates)
    if not ranked_chunks:
        return {"answer": NO_ANSWER_MESSAGE, "sources": []}
    llm_chunks = ranked_chunks[: min(top_k, LLM_TOP_K, 8)]

    try:
        answer = llm.answer(
            question,
            llm_chunks,
            answer_language=answer_language,
        ).strip()
    except OllamaError:
        raise

    sources = [
        {
            "source": chunk["source"],
            "page": chunk.get("page"),
            "text": chunk["text"][:300],
        }
        for chunk in chunks
    ]
    return {"answer": answer, "sources": sources}
