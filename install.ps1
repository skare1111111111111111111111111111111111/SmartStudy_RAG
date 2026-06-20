$ErrorActionPreference = "Stop"

$BaseDir = if ($env:SMARTSTUDY_DIR) { $env:SMARTSTUDY_DIR } else { "C:\SmartStudy_RAG" }
$ZipUrl = "https://github.com/Ffgags13/SmartStudy_RAG/archive/refs/heads/main.zip"
$ZipFile = Join-Path $env:TEMP "SmartStudy_RAG-main.zip"
$ProjectDir = Join-Path $BaseDir "SmartStudy_RAG-main"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker not found. Install Docker Desktop: https://www.docker.com/products/docker-desktop/"
}

Write-Host "Downloading SmartStudy RAG..."
New-Item -ItemType Directory -Force -Path $BaseDir | Out-Null
Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipFile -UseBasicParsing

Write-Host "Extracting to $BaseDir..."
if (Test-Path $ProjectDir) {
    Remove-Item -Recurse -Force $ProjectDir
}
Expand-Archive -Path $ZipFile -DestinationPath $BaseDir -Force
Remove-Item $ZipFile -Force

Set-Location $ProjectDir
.\run.ps1
