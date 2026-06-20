$ErrorActionPreference = "Stop"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker not found. Install Docker Desktop: https://www.docker.com/products/docker-desktop/"
}

$env:COMPOSE_BAKE = "false"

Write-Host "Pulling images (skip build if images exist on GHCR)..."
docker compose pull

Write-Host "Starting containers..."
docker compose up -d

Write-Host ""
Write-Host "SmartStudy RAG is starting."
Write-Host "  UI:  http://localhost:8501"
Write-Host "  API: http://localhost:8000/docs"
Write-Host ""
Write-Host "First run downloads LLM + embedding model and indexes documents (5-15 min)."
Write-Host "Progress: docker compose logs -f backend"
Write-Host ""
Write-Host "To rebuild locally: docker compose up --build -d"
