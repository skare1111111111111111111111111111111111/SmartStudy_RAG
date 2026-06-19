from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Вопрос пользователя")
    top_k: int = Field(default=5, ge=1, le=20, description="Сколько чанков искать")


class SourceItem(BaseModel):
    source: str
    page: int | None = None
    text: str


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceItem]


class StatsResponse(BaseModel):
    chunks_count: int
    documents: list[str]


class ReindexRequest(BaseModel):
    path: str | None = Field(default=None, description="Путь к папке или файлу")


class ReindexResponse(BaseModel):
    indexed_files: int
    chunks_added: int
    path: str


class HealthResponse(BaseModel):
    status: str
    ollama: str
