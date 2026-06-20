#!/usr/bin/env sh
set -e

if ! docker compose version >/dev/null 2>&1; then
  echo "Error: 'docker compose' not found."
  echo "Install Docker Desktop and enable WSL integration for your distro."
  exit 1
fi

export COMPOSE_BAKE=false
docker compose up --build -d

echo ""
echo "SmartStudy RAG is starting."
echo "  UI:  http://localhost:8501"
echo "  API: http://localhost:8000/docs"
echo ""
echo "First run downloads LLM + embedding model and indexes documents (5-15 min)."
echo "Progress: docker compose logs -f backend"
