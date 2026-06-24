import os
from pathlib import Path

from dotenv import load_dotenv

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_PROJECT_ROOT = _BACKEND_ROOT.parent

load_dotenv(_PROJECT_ROOT / ".env")


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _configure_cpu() -> None:
    threads = os.getenv("TORCH_NUM_THREADS", "2")
    os.environ.setdefault("OMP_NUM_THREADS", threads)
    os.environ.setdefault("MKL_NUM_THREADS", threads)
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


_configure_cpu()


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
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "8"))

DOCUMENTS_PATH = _resolve_path("DOCUMENTS_PATH", _PROJECT_ROOT / "data" / "documents")
CHROMA_PATH = _resolve_path("CHROMA_PATH", _PROJECT_ROOT / "data" / "chroma")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "400"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "30"))
TOP_K = int(os.getenv("TOP_K", "15"))
MAX_TOP_K = int(os.getenv("MAX_TOP_K", "100"))
LLM_TOP_K = int(os.getenv("LLM_TOP_K", "10"))

INDEX_ON_STARTUP = _env_bool("INDEX_ON_STARTUP", False)
WATCH_DOCUMENTS = _env_bool("WATCH_DOCUMENTS", True)
PREWARM_EMBEDDINGS = _env_bool("PREWARM_EMBEDDINGS", True)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "180"))
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "3072"))
OLLAMA_NUM_THREAD = int(os.getenv("OLLAMA_NUM_THREAD", "4"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_NUM_PREDICT = int(os.getenv("LLM_NUM_PREDICT", "320"))
LLM_MAX_CONTEXT_CHARS = int(os.getenv("LLM_MAX_CONTEXT_CHARS", "4500"))

HEALTH_CACHE_SECONDS = int(os.getenv("HEALTH_CACHE_SECONDS", "30"))
STATS_CACHE_SECONDS = int(os.getenv("STATS_CACHE_SECONDS", "30"))

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:8501,http://127.0.0.1:8501",
).split(",")
