"""SmartStudy RAG — backend-пакет."""

from src import config
from src.ingestion import (
    Indexer,
    chunk_pages,
    chunk_text,
    get_indexer,
    index_directory,
    index_file,
    parse_file,
)
from src.llm import (
    NO_ANSWER_MESSAGE,
    OllamaClient,
    OllamaError,
    get_llm_client,
)
from src.retrieval import (
    COLLECTION_NAME,
    DEFAULT_MODEL,
    VECTOR_SIZE,
    Embedder,
    Retriever,
    get_embedder,
    get_retriever,
)
from src.utils import (
    DocumentEventHandler,
    DocumentWatcher,
    get_watcher,
    is_supported_document,
)

__all__ = [
    "COLLECTION_NAME",
    "DEFAULT_MODEL",
    "DocumentEventHandler",
    "DocumentWatcher",
    "Embedder",
    "Indexer",
    "NO_ANSWER_MESSAGE",
    "OllamaClient",
    "OllamaError",
    "Retriever",
    "VECTOR_SIZE",
    "chunk_pages",
    "chunk_text",
    "config",
    "get_embedder",
    "get_indexer",
    "get_llm_client",
    "get_retriever",
    "get_watcher",
    "index_directory",
    "index_file",
    "is_supported_document",
    "parse_file",
]
