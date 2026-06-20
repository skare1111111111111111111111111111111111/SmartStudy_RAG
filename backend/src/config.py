import os
from pathlib import Path

from dotenv import load_dotenv

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_PROJECT_ROOT = _BACKEND_ROOT.parent

load_dotenv(_PROJECT_ROOT / ".env")


def _resolve_path(env_name: str, default: Path) -> str:
    raw = os.getenv(env_name)
    path = Path(raw) if raw else default
    if not path.is_absolute():
        path = _PROJECT_ROOT / path
    return str(path.resolve())


EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

DOCUMENTS_PATH = _resolve_path("DOCUMENTS_PATH", _PROJECT_ROOT / "data" / "documents")
CHROMA_PATH = _resolve_path("CHROMA_PATH", _PROJECT_ROOT / "data" / "chroma")

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
