"""Общий клиент Chroma — один экземпляр на путь, меньше RAM и блокировок."""

from __future__ import annotations

import chromadb
from chromadb.api.models.Collection import Collection

COLLECTION_NAME = "lectures"

_clients: dict[str, chromadb.ClientAPI] = {}
_collections: dict[tuple[str, str], Collection] = {}


def get_chroma_client(chroma_path: str) -> chromadb.ClientAPI:
    if chroma_path not in _clients:
        _clients[chroma_path] = chromadb.PersistentClient(path=chroma_path)
    return _clients[chroma_path]


def get_collection(
    chroma_path: str,
    collection_name: str = COLLECTION_NAME,
) -> Collection:
    key = (chroma_path, collection_name)
    if key not in _collections:
        client = get_chroma_client(chroma_path)
        _collections[key] = client.get_or_create_collection(name=collection_name)
    return _collections[key]


def reset_store(chroma_path: str | None = None) -> None:
    """Сброс кэша (для тестов)."""
    if chroma_path is None:
        _clients.clear()
        _collections.clear()
        return

    _clients.pop(chroma_path, None)
    to_remove = [key for key in _collections if key[0] == chroma_path]
    for key in to_remove:
        _collections.pop(key, None)
