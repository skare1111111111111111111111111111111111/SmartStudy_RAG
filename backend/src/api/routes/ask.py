from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from api.schemas import AskRequest, AskResponse, SourceItem
from api.services.llm import LLMClient, get_llm
from api.services.rag import ask
from retrieval.retriever import Retriever, get_retriever

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask_question(
    body: AskRequest,
    retriever: Retriever = Depends(get_retriever),
    llm: LLMClient = Depends(get_llm),
) -> AskResponse:
    try:
        result = ask(
            question=body.question,
            retriever=retriever,
            llm=llm,
            top_k=body.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Ошибка генерации ответа: {exc}",
        ) from exc

    return AskResponse(
        answer=result["answer"],
        sources=[SourceItem(**source) for source in result["sources"]],
    )
