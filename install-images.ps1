# Скачать только docker-compose и образы (без ZIP, без git, без сборки)
$ErrorActionPreference = "Stop"

$BaseDir = if ($env:SMARTSTUDY_DIR) { $env:SMARTSTUDY_DIR } else { "C:\SmartStudy_RAG" }
$ComposeUrl = "https://raw.githubusercontent.com/Ffgags13/SmartStudy_RAG/main/docker-compose.pull.yml"
$ComposeFile = Join-Path $BaseDir "docker-compose.yml"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker not found. Install Docker Desktop: https://www.docker.com/products/docker-desktop/"
}

Write-Host "Downloading docker-compose.yml..."
New-Item -ItemType Directory -Force -Path $BaseDir | Out-Null
Invoke-WebRequest -Uri $ComposeUrl -OutFile $ComposeFile -UseBasicParsing

Set-Location $BaseDir
$env:COMPOSE_BAKE = "false"

Write-Host "Pulling Docker images (no build, low RAM usage)..."
docker compose pull

Write-Host "Starting containers..."
docker compose up -d

Write-Host ""
Write-Host "SmartStudy RAG is starting."
Write-Host "  UI:  http://localhost:8501"
Write-Host "  API: http://localhost:8000/docs"
Write-Host ""
Write-Host "First run: LLM + embedding download (5-15 min)."
Write-Host "Progress: docker compose logs -f backend"
