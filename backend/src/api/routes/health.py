from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.schemas import HealthResponse
from src.llm import OllamaClient, get_llm_client

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(llm: OllamaClient = Depends(get_llm_client)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        ollama="available" if llm.is_available() else "unavailable",
    )
