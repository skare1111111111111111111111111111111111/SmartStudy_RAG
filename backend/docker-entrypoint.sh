#!/bin/sh
set -e

OLLAMA_URL="${OLLAMA_URL:-http://ollama:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2:1b}"

echo "Waiting for Ollama..."
until curl -sf "${OLLAMA_URL}/api/tags" > /dev/null 2>&1; do
  sleep 2
done
echo "Ollama is ready."

if ! curl -sf "${OLLAMA_URL}/api/tags" | grep -q "${OLLAMA_MODEL}"; then
  echo "Pulling ${OLLAMA_MODEL} (first run may take several minutes)..."
  curl -sf -X POST "${OLLAMA_URL}/api/pull" -d "{\"name\":\"${OLLAMA_MODEL}\"}" > /dev/null
  echo "Model ${OLLAMA_MODEL} is ready."
fi

echo "Checking document index..."
python -c "
from src.ingestion.indexer import get_indexer
from src.config import DOCUMENTS_PATH
idx = get_indexer()
if idx.count() == 0:
    n = idx.index_directory(DOCUMENTS_PATH)
    print(f'Indexed {n} chunks from {DOCUMENTS_PATH}')
else:
    print(f'Index already has {idx.count()} chunks')
"

exec "$@"
