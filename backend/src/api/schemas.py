from __future__ import annotations

from pydantic import BaseModel, Field

from src.config import MAX_TOP_K, TOP_K


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Вопрос пользователя")
    top_k: int = Field(default=TOP_K, ge=1, le=MAX_TOP_K, description="Сколько чанков искать")
    answer_language: str | None = Field(
        default=None,
        min_length=2,
        max_length=32,
        description="Язык ответа (например: ru, en, de). Если пусто, определяется автоматически.",
    )


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


class UploadResponse(BaseModel):
    filename: str
    chunks_added: int
    path: str


class HealthResponse(BaseModel):
    status: str
    ollama: str
