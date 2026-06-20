#!/usr/bin/env sh
set -e

BASE_DIR="${SMARTSTUDY_DIR:-$HOME/SmartStudy_RAG}"
COMPOSE_URL="https://raw.githubusercontent.com/Ffgags13/SmartStudy_RAG/main/docker-compose.pull.yml"

command -v docker >/dev/null 2>&1 || { echo "Docker not found"; exit 1; }

mkdir -p "$BASE_DIR"
echo "Downloading docker-compose.yml..."
curl -fsSL "$COMPOSE_URL" -o "$BASE_DIR/docker-compose.yml"

cd "$BASE_DIR"
export COMPOSE_BAKE=false

echo "Pulling Docker images..."
docker compose pull

echo "Starting containers..."
docker compose up -d

echo ""
echo "UI:  http://localhost:8501"
echo "API: http://localhost:8000/docs"
