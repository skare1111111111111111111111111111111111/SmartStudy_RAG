import os
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
CHROMA_PATH = os.getenv("CHROMA_PATH", str(_BACKEND_ROOT / "chroma_storage"))
DOCUMENTS_PATH = os.getenv(
    "DOCUMENTS_PATH",
    str(_BACKEND_ROOT / "src" / "ingestion" / "documents"),
)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
TOP_K = int(os.getenv("TOP_K", "5"))
