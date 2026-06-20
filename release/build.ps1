# Build SmartStudy-Setup.exe (Python 3.12 + PS2EXE fallback)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ReleaseDir = Join-Path $Root "release"
$DistDir = Join-Path $ReleaseDir "dist"
$ScriptsDir = Join-Path $Root "scripts"

function Find-Python312 {
    foreach ($cmd in @("py -3.12", "python3.12", "python")) {
        try {
            $v = Invoke-Expression "$cmd --version 2>&1"
            if ($v -match "3\.12") { return $cmd.Split(" ")[0] + $(if ($cmd -match "-3.12") { " -3.12" } else { "" }) }
        } catch {}
    }
    throw "Python 3.12 required. Install from python.org (avoid 3.14 for onefile builds)."
}

Write-Host "Building SmartStudy RAG installers..." -ForegroundColor Cyan

# --- Python onefile (PyInstaller 3.12) ---
$py = Find-Python312
Write-Host "Using: $py"
Invoke-Expression "$py -m pip install -q -r `"$(Join-Path $ReleaseDir 'requirements-build.txt')`""

Push-Location $ReleaseDir
try {
    foreach ($d in @("build", "build-portable", "dist")) {
        if (Test-Path $d) { Remove-Item -Recurse -Force $d }
    }

    Invoke-Expression "$py -m PyInstaller --onefile --console --noupx --name SmartStudy-Setup --distpath dist --workpath build --specpath build --clean installer.py"
    Invoke-Expression "$py -m PyInstaller --onedir --console --noupx --name SmartStudy-Setup-Portable --distpath dist --workpath build-portable --specpath build-portable --clean installer.py"

    $exe = Join-Path $DistDir "SmartStudy-Setup.exe"
    if (-not (Test-Path $exe)) { throw "PyInstaller failed" }
    $hash = (Get-FileHash $exe -Algorithm SHA256).Hash
    Set-Content (Join-Path $DistDir "SmartStudy-Setup.exe.sha256") "$hash  SmartStudy-Setup.exe"
    Write-Host "  SmartStudy-Setup.exe OK (Python 3.12 onefile)" -ForegroundColor Green
} finally {
    Pop-Location
}

# --- PowerShell native exe (no Python runtime, most reliable) ---
if (-not (Get-Module -ListAvailable ps2exe)) {
    Install-Module ps2exe -Force -Scope CurrentUser
}
Import-Module ps2exe
Invoke-ps2exe -inputFile (Join-Path $ScriptsDir "SmartStudy-Setup.ps1") `
    -outputFile (Join-Path $DistDir "SmartStudy-Setup-PS.exe") `
    -noConsole:$false -title "SmartStudy RAG Setup"
Write-Host "  SmartStudy-Setup-PS.exe OK (PowerShell, no PyInstaller)" -ForegroundColor Green

# --- Portable zip (onedir, if onefile extraction fails) ---
$portableZip = Join-Path $DistDir "SmartStudy-Setup-Portable.zip"
Compress-Archive -Path (Join-Path $DistDir "SmartStudy-Setup-Portable") -DestinationPath $portableZip -Force
Write-Host "  SmartStudy-Setup-Portable.zip OK" -ForegroundColor Green

Write-Host ""
Write-Host "Output: $DistDir"
Write-Host "SHA256: $hash"
Write-Host ""
Write-Host "If onefile fails with PYI-16524, use SmartStudy-Setup-PS.exe or Portable.zip"
