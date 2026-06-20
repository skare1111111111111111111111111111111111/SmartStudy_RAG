#!/usr/bin/env sh
set -e
docker compose up --build -d
echo ""
echo "SmartStudy RAG is starting."
echo "  UI:  http://localhost:8501"
echo "  API: http://localhost:8000/docs"
echo ""
echo "First run downloads LLM + embedding model and indexes documents (5-15 min)."
echo "Progress: docker compose logs -f backend"
