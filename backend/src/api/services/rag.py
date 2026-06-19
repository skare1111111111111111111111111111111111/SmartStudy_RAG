from __future__ import annotations

from typing import Any

from src.llm import NO_ANSWER_MESSAGE, OllamaClient, OllamaError
from src.retrieval import Retriever


def ask(
    question: str,
    retriever: Retriever,
    llm: OllamaClient,
    top_k: int = 5,
) -> dict[str, Any]:
    """RAG-пайплайн: поиск чанков → ответ LLM."""
    chunks = retriever.search(question, top_k=top_k)

    if not chunks:
        return {"answer": NO_ANSWER_MESSAGE, "sources": []}

    try:
        answer = llm.answer(question, chunks).strip()
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
