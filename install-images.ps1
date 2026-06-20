# Установка SmartStudy RAG: pull готовых образов или fallback на ZIP + сборку
$ErrorActionPreference = "Stop"

$BaseDir = if ($env:SMARTSTUDY_DIR) { $env:SMARTSTUDY_DIR } else { "C:\SmartStudy_RAG" }
$ComposeUrl = "https://raw.githubusercontent.com/Ffgags13/SmartStudy_RAG/main/docker-compose.pull.yml"
$ComposeFile = Join-Path $BaseDir "docker-compose.yml"
$BackendImage = "ghcr.io/ffgags13/smartstudy-rag-backend:latest"

function Test-DockerEngine {
    $info = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Docker Engine не отвечает (часто после сбоя Docker Desktop)." -ForegroundColor Yellow
        Write-Host "  1. Quit Docker Desktop -> запустить снова -> дождаться 'Engine running'"
        Write-Host "  2. Или: Settings -> Troubleshoot -> Reset to factory defaults"
        Write-Host "  3. Подробнее: docs/DOCKER_RECOVERY.md в репозитории"
        throw "Docker Engine unavailable"
    }
}

function Install-FromZip {
    $ZipUrl = "https://github.com/Ffgags13/SmartStudy_RAG/archive/refs/heads/main.zip"
    $ZipFile = Join-Path $env:TEMP "SmartStudy_RAG-main.zip"
    $ProjectDir = Join-Path $BaseDir "SmartStudy_RAG-main"

    Write-Host ""
    Write-Host "Fallback: скачивание исходников и локальная сборка образов..." -ForegroundColor Yellow
    Write-Host "(Образы GHCR ещё не опубликованы — это нормально до первой сборки в Actions)"
    Write-Host ""

    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipFile -UseBasicParsing
    if (Test-Path $ProjectDir) {
        Remove-Item -Recurse -Force $ProjectDir
    }
    Expand-Archive -Path $ZipFile -DestinationPath $BaseDir -Force
    Remove-Item $ZipFile -Force

    Set-Location $ProjectDir
    $env:COMPOSE_BAKE = "false"
    docker compose up --build -d
    return $ProjectDir
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker not found. Install Docker Desktop: https://www.docker.com/products/docker-desktop/"
}

Test-DockerEngine

Write-Host "Downloading docker-compose.yml..."
New-Item -ItemType Directory -Force -Path $BaseDir | Out-Null
Invoke-WebRequest -Uri $ComposeUrl -OutFile $ComposeFile -UseBasicParsing

Set-Location $BaseDir
$env:COMPOSE_BAKE = "false"

Write-Host "Checking GHCR images..."
docker pull $BackendImage 2>&1 | Out-Host
$pullOk = ($LASTEXITCODE -eq 0)

if (-not $pullOk) {
    Write-Host ""
    Write-Host "Не удалось скачать $BackendImage" -ForegroundColor Yellow
    Write-Host "Причины: образ ещё не собран в GitHub Actions, или Docker Desktop нестабилен (500 Internal Server Error)."
    Install-FromZip | Out-Null
} else {
    Write-Host "Pulling remaining images..."
    docker compose pull
    if ($LASTEXITCODE -ne 0) {
        Install-FromZip | Out-Null
    } else {
        Write-Host "Starting containers..."
        docker compose up -d
    }
}

Write-Host ""
Write-Host "SmartStudy RAG is starting."
Write-Host "  UI:  http://localhost:8501"
Write-Host "  API: http://localhost:8000/docs"
Write-Host ""
Write-Host "First run: LLM + embedding download (5-15 min)."
Write-Host "Progress: docker compose logs -f backend"
