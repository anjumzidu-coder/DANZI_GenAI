$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$pythonCandidates = @(
    (Join-Path $PSScriptRoot ".venv\Scripts\python.exe"),
    (Join-Path (Split-Path $PSScriptRoot -Parent) ".venv\Scripts\python.exe")
)

if ($env:VIRTUAL_ENV) {
    $pythonCandidates = @((Join-Path $env:VIRTUAL_ENV "Scripts\python.exe")) + $pythonCandidates
}

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $pythonCandidates += $pythonCmd.Source
}

$pythonCandidates += "C:\Python314\python.exe"

$python = $pythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not (Test-Path $python)) {
    throw "Python runtime not found. Install Python or activate your virtual environment first."
}

Write-Host "Using Python: $python" -ForegroundColor Cyan

Write-Host "Installing app dependencies..." -ForegroundColor Cyan
& $python -m pip install -r requirements.txt

Write-Host "Installing/Updating packaging dependencies..." -ForegroundColor Cyan
& $python -m pip install --upgrade pip pyinstaller

Write-Host "Building local EXE..." -ForegroundColor Cyan
& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name "HPE_SS_Tool_Local" `
    --collect-all streamlit `
    --collect-all pandas `
    --collect-all openpyxl `
    --collect-all pypdf `
    --collect-all pptx `
    --add-data "app.py;." `
    --add-data "src;src" `
    --add-data ".env.example;." `
    ss_tool_local_launcher.py

$exePath = Join-Path $PSScriptRoot "dist\HPE_SS_Tool_Local.exe"
if (-not (Test-Path $exePath)) {
    throw "Build finished but EXE not found at $exePath"
}

Write-Host "";
Write-Host "Build completed." -ForegroundColor Green
Write-Host "EXE: $exePath" -ForegroundColor Green
Write-Host ""
Write-Host "Share this EXE with teammates." -ForegroundColor Yellow
Write-Host "Each teammate can run it locally without cloud deployment." -ForegroundColor Yellow
