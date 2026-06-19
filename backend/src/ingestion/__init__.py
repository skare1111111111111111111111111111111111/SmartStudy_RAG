"""Индексация документов: парсер → чанкер → Chroma."""

from .chunker import chunk_pages, chunk_text
from .indexer import Indexer, get_indexer, index_directory, index_file
from .parser import SUPPORTED_EXTENSIONS, parse_file

__all__ = [
    "Indexer",
    "SUPPORTED_EXTENSIONS",
    "chunk_pages",
    "chunk_text",
    "get_indexer",
    "index_directory",
    "index_file",
    "parse_file",
]
