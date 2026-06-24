from __future__ import annotations

import asyncio
from functools import partial
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from src.api.routes.stats import invalidate_stats_cache
from src.api.schemas import UploadResponse
from src.config import DOCUMENTS_PATH
from src.ingestion import SUPPORTED_EXTENSIONS, Indexer, get_indexer

router = APIRouter(tags=["documents"])


def _safe_filename(name: str) -> str:
    filename = Path(name).name
    if not filename or filename in {".", ".."}:
        raise HTTPException(status_code=400, detail="Некорректное имя файла")

    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат: {suffix or '(нет)'}. Поддерживаются: {supported}",
        )
    return filename


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    indexer: Indexer = Depends(get_indexer),
) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Имя файла не указано")

    filename = _safe_filename(file.filename)
    documents_dir = Path(DOCUMENTS_PATH)
    documents_dir.mkdir(parents=True, exist_ok=True)
    destination = documents_dir / filename

    content = await file.read()
    if not content.strip():
        raise HTTPException(status_code=400, detail="Файл пустой")

    destination.write_bytes(content)

    loop = asyncio.get_running_loop()
    try:
        chunks_added = await loop.run_in_executor(
            None,
            partial(indexer.index_file, destination, force=True),
        )
    except ValueError as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    invalidate_stats_cache()

    return UploadResponse(
        filename=filename,
        chunks_added=chunks_added,
        path=str(destination),
    )
