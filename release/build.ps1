# Build SmartStudy-Setup.exe
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ReleaseDir = Join-Path $Root "release"
$DistDir = Join-Path $ReleaseDir "dist"

Write-Host "Building SmartStudy-Setup.exe..."

py -m pip install -q -r (Join-Path $ReleaseDir "requirements-build.txt")

Push-Location $ReleaseDir
try {
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

    py -m PyInstaller `
        --onefile `
        --console `
        --name "SmartStudy-Setup" `
        --distpath "dist" `
        --workpath "build" `
        --specpath "build" `
        --clean `
        "installer.py"

    $exe = Join-Path $DistDir "SmartStudy-Setup.exe"
    if (-not (Test-Path $exe)) { throw "Build failed: $exe not found" }

    $hash = (Get-FileHash $exe -Algorithm SHA256).Hash
    Write-Host ""
    Write-Host "OK: $exe" -ForegroundColor Green
    Write-Host "SHA256: $hash"
    Set-Content -Path (Join-Path $DistDir "SmartStudy-Setup.exe.sha256") -Value "$hash  SmartStudy-Setup.exe"
} finally {
    Pop-Location
}
