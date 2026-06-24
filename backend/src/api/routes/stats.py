from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from src.api.schemas import StatsResponse
from src.config import STATS_CACHE_SECONDS
from src.ingestion.indexer import Indexer, get_indexer
from src.retrieval import Retriever, get_retriever

router = APIRouter(tags=["stats"])

_stats_cache: tuple[float, StatsResponse] | None = None


def _get_stats(
    retriever: Retriever,
    indexer: Indexer,
) -> StatsResponse:
    global _stats_cache

    now = time.monotonic()
    if _stats_cache is not None:
        cached, ts = _stats_cache
        if now - ts < STATS_CACHE_SECONDS:
            return cached

    response = StatsResponse(
        chunks_count=retriever.count(),
        documents=indexer.list_sources(),
    )
    _stats_cache = (response, now)
    return response


def invalidate_stats_cache() -> None:
    global _stats_cache
    _stats_cache = None


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    retriever: Retriever = Depends(get_retriever),
    indexer: Indexer = Depends(get_indexer),
) -> StatsResponse:
    return _get_stats(retriever, indexer)
