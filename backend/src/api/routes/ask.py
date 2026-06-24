from __future__ import annotations

import asyncio
from functools import partial

from fastapi import APIRouter, Depends, HTTPException

from src.api.schemas import AskRequest, AskResponse, SourceItem
from src.api.services.rag import ask
from src.llm import OllamaClient, OllamaError, get_llm_client
from src.retrieval import Retriever, get_retriever

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    body: AskRequest,
    retriever: Retriever = Depends(get_retriever),
    llm: OllamaClient = Depends(get_llm_client),
) -> AskResponse:
    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(
            None,
            partial(
                ask,
                question=body.question,
                retriever=retriever,
                llm=llm,
                top_k=body.top_k,
                answer_language=body.answer_language,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return AskResponse(
        answer=result["answer"],
        sources=[SourceItem(**source) for source in result["sources"]],
    )
