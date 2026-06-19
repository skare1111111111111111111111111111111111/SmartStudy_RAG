from __future__ import annotations

from typing import Any

from api.services.llm import LLMClient
from retrieval.retriever import Retriever

PROMPT_TEMPLATE = """Ты — ассистент студента. Ответь на вопрос, используя ТОЛЬКО следующий контекст.
Если в контексте нет ответа, скажи: «В загруженных документах ответ не найден».

КОНТЕКСТ:
{context}

ВОПРОС: {question}

ОТВЕТ:"""

NOT_FOUND_ANSWER = "В загруженных документах ответ не найден."


def format_context(chunks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        page = chunk.get("page", "?")
        source = chunk.get("source", "unknown")
        parts.append(f"[{index}] ({source}, стр. {page}): {chunk['text']}")
    return "\n\n".join(parts)


def ask(
    question: str,
    retriever: Retriever,
    llm: LLMClient,
    top_k: int = 5,
) -> dict[str, Any]:
    """RAG-пайплайн: поиск чанков → промпт → ответ LLM."""
    chunks = retriever.search(question, top_k=top_k)

    if not chunks:
        return {"answer": NOT_FOUND_ANSWER, "sources": []}

    prompt = PROMPT_TEMPLATE.format(
        context=format_context(chunks),
        question=question.strip(),
    )
    answer = llm.generate(prompt).strip()

    sources = [
        {
            "source": chunk["source"],
            "page": chunk.get("page"),
            "text": chunk["text"][:300],
        }
        for chunk in chunks
    ]
    return {"answer": answer, "sources": sources}
