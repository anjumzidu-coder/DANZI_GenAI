$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$python = "C:\Python314\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Python not found at $python" -ForegroundColor Red
    exit 1
}

$ip = (Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notlike '169.254*' -and $_.IPAddress -ne '127.0.0.1' } |
    Select-Object -First 1 -ExpandProperty IPAddress)

if (-not $ip) {
    $ip = "localhost"
}

Write-Host ""
Write-Host "Starting Excel AI Agent for team access..." -ForegroundColor Green
Write-Host "Local URL:   http://localhost:8501"
Write-Host "Team URL:    http://$ip`:8501"
Write-Host ""

& $python -m streamlit run app.py
