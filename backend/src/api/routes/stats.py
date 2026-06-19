from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.schemas import StatsResponse
from src.retrieval import Retriever, get_retriever

router = APIRouter(tags=["stats"])


def _list_documents(retriever: Retriever) -> list[str]:
    if retriever.count() == 0:
        return []

    data = retriever.collection.get(include=["metadatas"])
    sources: set[str] = set()
    for metadata in data.get("metadatas") or []:
        if metadata and metadata.get("source"):
            sources.add(metadata["source"])
    return sorted(sources)


@router.get("/stats", response_model=StatsResponse)
def get_stats(retriever: Retriever = Depends(get_retriever)) -> StatsResponse:
    return StatsResponse(
        chunks_count=retriever.count(),
        documents=_list_documents(retriever),
    )
