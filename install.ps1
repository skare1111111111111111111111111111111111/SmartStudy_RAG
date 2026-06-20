$ErrorActionPreference = "Stop"
$Repo = if ($env:SMARTSTUDY_REPO) { $env:SMARTSTUDY_REPO } else { "https://github.com/Ffgags13/SmartStudy_RAG.git" }
$Dir = if ($env:SMARTSTUDY_DIR) { $env:SMARTSTUDY_DIR } else { "SmartStudy_RAG" }
git clone --depth 1 $Repo $Dir
Set-Location $Dir
.\run.ps1
