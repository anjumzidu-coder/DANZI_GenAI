$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$packageDir = Join-Path $PSScriptRoot "release\HPE_SS_Tool_Local_Package_Extracted"
$zipPath = Join-Path $PSScriptRoot "release\HPE_SS_Tool_Local_Package.zip"
$distExe = Join-Path $PSScriptRoot "dist\HPE_SS_Tool_Local.exe"
$envTemplate = Join-Path $PSScriptRoot ".env.example"
$issFile = Join-Path $PSScriptRoot "installer\HPE_SS_Tool_Local.iss"

if (-not (Test-Path $issFile)) {
    throw "Missing installer script: $issFile"
}

if (-not (Test-Path $packageDir)) {
    New-Item -ItemType Directory -Path $packageDir | Out-Null
}

if ((-not (Test-Path (Join-Path $packageDir "HPE_SS_Tool_Local.exe"))) -and (Test-Path $distExe)) {
    Copy-Item $distExe (Join-Path $packageDir "HPE_SS_Tool_Local.exe") -Force
}

if ((-not (Test-Path (Join-Path $packageDir ".env.example"))) -and (Test-Path $envTemplate)) {
    Copy-Item $envTemplate (Join-Path $packageDir ".env.example") -Force
}

if ((-not (Test-Path (Join-Path $packageDir "HPE_SS_Tool_Local.exe"))) -and (Test-Path $zipPath)) {
    Expand-Archive -Path $zipPath -DestinationPath $packageDir -Force
}

if (-not (Test-Path (Join-Path $packageDir "HPE_SS_Tool_Local.exe"))) {
    throw "Package input missing. Build the EXE first with build_local_exe.ps1."
}

$isccCmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if ($isccCmd) {
    $isccPath = $isccCmd.Source
} else {
    $candidates = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
    )

    $isccPath = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $isccPath) {
    throw "Inno Setup compiler not found. Install it with: winget install --id JRSoftware.InnoSetup"
}

Write-Host "Using ISCC: $isccPath" -ForegroundColor Cyan
& $isccPath $issFile

if ($LASTEXITCODE -ne 0) {
    throw "Installer build failed."
}

$output = Join-Path $PSScriptRoot "release\installer\HPE_SS_Tool_Local_Installer.exe"
if (-not (Test-Path $output)) {
    throw "Installer build completed but output not found at $output"
}

Write-Host "";
Write-Host "Installer created successfully:" -ForegroundColor Green
Write-Host $output -ForegroundColor Green
