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

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_NUM_PREDICT = int(os.getenv("LLM_NUM_PREDICT", "512"))

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:8501,http://127.0.0.1:8501",
).split(",")
