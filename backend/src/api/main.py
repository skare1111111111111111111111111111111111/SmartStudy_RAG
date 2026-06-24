from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.ask import router as ask_router
from src.api.routes.documents import router as documents_router
from src.api.routes.health import router as health_router
from src.api.routes.reindex import router as reindex_router
from src.api.routes.stats import router as stats_router
from src.config import (
    CORS_ORIGINS,
    DOCUMENTS_PATH,
    INDEX_ON_STARTUP,
    PREWARM_EMBEDDINGS,
    WATCH_DOCUMENTS,
)
from src.ingestion.indexer import get_indexer
from src.retrieval.embedding import get_embedder
from src.utils import get_watcher

logger = logging.getLogger(__name__)


def _index_if_empty() -> None:
    try:
        indexer = get_indexer()
        if indexer.count() > 0:
            logger.info("Index already has %d chunks, skipping startup indexing", indexer.count())
            return

        count = indexer.index_directory(DOCUMENTS_PATH)
        logger.info("Background startup indexing: %d chunks", count)
    except Exception:
        logger.exception("Startup indexing failed")


def _prewarm_embedder() -> None:
    try:
        get_embedder().encode("warmup")
        logger.info("Embedding model pre-warmed")
    except Exception:
        logger.exception("Embedding pre-warm failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if PREWARM_EMBEDDINGS:
        threading.Thread(target=_prewarm_embedder, daemon=True).start()

    if INDEX_ON_STARTUP:
        thread = threading.Thread(target=_index_if_empty, daemon=True)
        thread.start()

    if WATCH_DOCUMENTS:
        watcher = get_watcher()
        watcher.start(index_existing=False)
        yield
        watcher.stop()
    else:
        yield


app = FastAPI(
    title="SmartStudy RAG API",
    description="REST API для вопросов по учебным материалам",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(ask_router)
app.include_router(stats_router)
app.include_router(reindex_router)
app.include_router(documents_router)
