# SmartStudy RAG — установщик (Docker pull / ZIP / локальная копия)
param(
    [string]$BaseDir = $(if ($env:SMARTSTUDY_DIR) { $env:SMARTSTUDY_DIR } else { "C:\SmartStudy_RAG" }),
    [string]$LocalRepo = $env:SMARTSTUDY_LOCAL_REPO,
    [switch]$BuildOnly,
    [switch]$PullOnly,
    [switch]$SkipWslFix
)

$ErrorActionPreference = "Stop"
$ComposeUrl = "https://raw.githubusercontent.com/Ffgags13/SmartStudy_RAG/main/docker-compose.pull.yml"
$ZipUrl = "https://github.com/Ffgags13/SmartStudy_RAG/archive/refs/heads/main.zip"
$BackendImage = "ghcr.io/ffgags13/smartstudy-rag-backend:latest"

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

function Test-DockerEngine {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Docker Engine не отвечает. Запустите Docker Desktop." -ForegroundColor Yellow
        throw "Docker Engine unavailable"
    }
}

function Fix-WslVpnRoutes {
    if ($SkipWslFix) { return }
    $vpn = Get-NetRoute -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.InterfaceAlias -match 'Amnezia|WireGuard|OpenVPN|TAP' -and $_.DestinationPrefix -match '^172\.(1[6-9]|2[0-9]|3[01])\.' -and $_.DestinationPrefix -ne '0.0.0.0/0' }
    foreach ($r in $vpn) {
        Write-Host "  VPN route fix: remove $($r.DestinationPrefix) from $($r.InterfaceAlias)"
        Remove-NetRoute -DestinationPrefix $r.DestinationPrefix -InterfaceAlias $r.InterfaceAlias -Confirm:$false -ErrorAction SilentlyContinue
    }
    if ($vpn) { wsl --shutdown 2>$null; Start-Sleep -Seconds 2 }
}

function Install-FromLocal {
    param([string]$Source, [string]$Target)
    Write-Step "Copy local repo: $Source"
    if (-not (Test-Path (Join-Path $Source "docker-compose.yml"))) {
        throw "Not a SmartStudy repo: $Source"
    }
    if (Test-Path $Target) { Remove-Item -Recurse -Force $Target }
    New-Item -ItemType Directory -Force -Path (Split-Path $Target) | Out-Null
    Copy-Item -Path $Source -Destination $Target -Recurse -Force
    return $Target
}

function Install-FromZip {
    $ZipFile = Join-Path $env:TEMP "SmartStudy_RAG-main.zip"
    $ProjectDir = Join-Path $BaseDir "SmartStudy_RAG-main"
    Write-Step "Download ZIP from GitHub"
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipFile -UseBasicParsing
    if (Test-Path $ProjectDir) { Remove-Item -Recurse -Force $ProjectDir }
    Expand-Archive -Path $ZipFile -DestinationPath $BaseDir -Force
    Remove-Item $ZipFile -Force
    return $ProjectDir
}

function Start-Compose {
    param([string]$ProjectDir, [switch]$Build)
    Set-Location $ProjectDir
    $env:COMPOSE_BAKE = "false"
    if ($Build) {
        docker compose up --build -d
    } else {
        docker compose pull
        docker compose up -d
    }
}

function Install-PullOnly {
    $ComposeFile = Join-Path $BaseDir "docker-compose.yml"
    Write-Step "Pull-only mode"
    New-Item -ItemType Directory -Force -Path $BaseDir | Out-Null
    Invoke-WebRequest -Uri $ComposeUrl -OutFile $ComposeFile -UseBasicParsing
    Set-Location $BaseDir
    $env:COMPOSE_BAKE = "false"
    docker compose pull
    docker compose up -d
}

Write-Host @"

 SmartStudy RAG Setup
 BaseDir: $BaseDir

"@ -ForegroundColor Green

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker not found. Install: https://www.docker.com/products/docker-desktop/"
}

Fix-WslVpnRoutes
Test-DockerEngine
New-Item -ItemType Directory -Force -Path $BaseDir | Out-Null

if ($PullOnly) {
    Install-PullOnly
} else {
    $projectDir = $null
    $usedPull = $false

    if (-not $BuildOnly) {
        Write-Step "Try GHCR images"
        try {
            docker pull $BackendImage 2>&1 | Out-Host
            if ($LASTEXITCODE -eq 0) {
                Install-PullOnly
                $usedPull = $true
            }
        } catch { }
    }

    if (-not $usedPull) {
        if ($LocalRepo -and (Test-Path $LocalRepo)) {
            $projectDir = Install-FromLocal -Source $LocalRepo -Target (Join-Path $BaseDir "SmartStudy_RAG-main")
        } elseif ($env:SMARTSTUDY_LOCAL_REPO -and (Test-Path $env:SMARTSTUDY_LOCAL_REPO)) {
            $projectDir = Install-FromLocal -Source $env:SMARTSTUDY_LOCAL_REPO -Target (Join-Path $BaseDir "SmartStudy_RAG-main")
        } else {
            try {
                $projectDir = Install-FromZip
            } catch {
                Write-Host "GitHub недоступен. Укажите локальный путь:" -ForegroundColor Yellow
                Write-Host '  $env:SMARTSTUDY_LOCAL_REPO="C:\path\to\SmartStudy_RAG"; .\SmartStudy-Setup.ps1'
                throw
            }
        }
        Start-Compose -ProjectDir $projectDir -Build
    }
}

Write-Host @"

 Done.
   UI:  http://localhost:8501
   API: http://localhost:8000/docs
   Logs: docker compose logs -f backend

"@ -ForegroundColor Green
