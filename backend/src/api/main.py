from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.ask import router as ask_router
from src.api.routes.health import router as health_router
from src.api.routes.reindex import router as reindex_router
from src.api.routes.stats import router as stats_router
from src.config import CORS_ORIGINS
from src.utils import get_watcher


@asynccontextmanager
async def lifespan(app: FastAPI):
    watcher = get_watcher()
    watcher.start(index_existing=True)
    yield
    watcher.stop()


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
