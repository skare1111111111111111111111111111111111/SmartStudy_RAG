from __future__ import annotations

from fastapi import APIRouter, Depends

from api.schemas import HealthResponse
from api.services.llm import LLMClient, get_llm

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(llm: LLMClient = Depends(get_llm)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        ollama="available" if llm.is_available() else "unavailable",
    )
