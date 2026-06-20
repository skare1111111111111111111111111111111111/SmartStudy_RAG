"""Утилиты: авто-переиндексация и вспомогательные функции."""

from .file_watcher import (
    IGNORED_SUFFIXES,
    DocumentEventHandler,
    DocumentWatcher,
    get_watcher,
    is_supported_document,
)

__all__ = [
    "IGNORED_SUFFIXES",
    "DocumentEventHandler",
    "DocumentWatcher",
    "get_watcher",
    "is_supported_document",
]
