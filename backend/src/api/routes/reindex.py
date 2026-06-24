from __future__ import annotations

import asyncio
from functools import partial
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from src.api.routes.stats import invalidate_stats_cache
from src.api.schemas import ReindexRequest, ReindexResponse
from src.config import DOCUMENTS_PATH
from src.ingestion import SUPPORTED_EXTENSIONS, Indexer, get_indexer

router = APIRouter(tags=["reindex"])


def _count_files(path: Path) -> int:
    if path.is_file():
        return 1 if path.suffix.lower() in SUPPORTED_EXTENSIONS else 0

    count = 0
    for ext in SUPPORTED_EXTENSIONS:
        count += len(list(path.glob(f"*{ext}")))
    return count


@router.post("/reindex", response_model=ReindexResponse)
async def reindex_documents(
    body: ReindexRequest,
    indexer: Indexer = Depends(get_indexer),
) -> ReindexResponse:
    target = Path(body.path) if body.path else Path(DOCUMENTS_PATH)

    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Путь не найден: {target}")

    loop = asyncio.get_running_loop()

    try:
        if target.is_file():
            chunks_added = await loop.run_in_executor(
                None,
                partial(indexer.index_file, target, force=True),
            )
            indexed_files = 1 if chunks_added >= 0 else 0
        else:
            indexed_files = _count_files(target)
            chunks_added = await loop.run_in_executor(
                None,
                partial(indexer.index_directory, target, force=True),
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    invalidate_stats_cache()

    return ReindexResponse(
        indexed_files=indexed_files,
        chunks_added=chunks_added,
        path=str(target),
    )
