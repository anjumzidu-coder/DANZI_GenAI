param(
    [Parameter(Mandatory = $true)]
    [string]$SubscriptionId,

    [Parameter(Mandatory = $true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory = $true)]
    [string]$Location,

    [Parameter(Mandatory = $true)]
    [string]$WebAppName,

    [Parameter(Mandatory = $true)]
    [string]$AcrName,

    [string]$PlanName = "ss-tool-plan",
    [string]$ImageName = "ss-tool",
    [string]$ImageTag = "latest",
    [string]$EnvFile = ".env",
    [switch]$SkipEnvImport
)

$ErrorActionPreference = "Stop"

function Ensure-AzOnPath {
    if (Get-Command az -ErrorAction SilentlyContinue) {
        return
    }

    $azDirCandidates = @(
        "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin",
        "C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin"
    )

    foreach ($dir in $azDirCandidates) {
        if (Test-Path (Join-Path $dir "az.cmd")) {
            $env:Path = "$env:Path;$dir"
            break
        }
    }
}

function Assert-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found. Install it and retry."
    }
}

function Invoke-Az {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args,
        [string]$FailureMessage = "Azure CLI command failed."
    )

    & az @Args
    if ($LASTEXITCODE -ne 0) {
        throw $FailureMessage
    }
}

function Load-EnvSettings {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        Write-Host "Env file not found at $Path. Skipping app settings import." -ForegroundColor Yellow
        return @()
    }

    $pairs = @()
    $lines = Get-Content -Path $Path
    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }

        $parts = $trimmed -split "=", 2
        if ($parts.Count -ne 2) {
            continue
        }

        $key = $parts[0].Trim()
        $value = $parts[1].Trim()
        if ($key) {
            $pairs += "$key=$value"
        }
    }

    return $pairs
}

Ensure-AzOnPath
Assert-Command -Name "az"

Invoke-Az -Args @("account", "show") -FailureMessage "Azure CLI is not logged in. Run 'az login' and retry." | Out-Null

Set-Location $PSScriptRoot

Write-Host "Setting subscription..." -ForegroundColor Cyan
Invoke-Az -Args @("account", "set", "--subscription", $SubscriptionId) -FailureMessage "Failed to set Azure subscription."

Write-Host "Ensuring resource group..." -ForegroundColor Cyan
Invoke-Az -Args @("group", "create", "--name", $ResourceGroup, "--location", $Location) -FailureMessage "Failed to create or access resource group." | Out-Null

Write-Host "Ensuring App Service plan..." -ForegroundColor Cyan
Invoke-Az -Args @("appservice", "plan", "create", "--name", $PlanName, "--resource-group", $ResourceGroup, "--location", $Location, "--is-linux", "--sku", "B1") -FailureMessage "Failed to create or access App Service plan." | Out-Null

Write-Host "Ensuring Azure Container Registry..." -ForegroundColor Cyan
Invoke-Az -Args @("acr", "create", "--name", $AcrName, "--resource-group", $ResourceGroup, "--location", $Location, "--sku", "Basic", "--admin-enabled", "true") -FailureMessage "Failed to create or access Azure Container Registry." | Out-Null

$imageRef = "${AcrName}.azurecr.io/${ImageName}:${ImageTag}"

Write-Host "Building and pushing container image to ACR..." -ForegroundColor Cyan
Invoke-Az -Args @("acr", "build", "--registry", $AcrName, "--image", "${ImageName}:${ImageTag}", ".") -FailureMessage "Failed to build and push image to ACR."

Write-Host "Ensuring web app..." -ForegroundColor Cyan
$existing = (& az webapp list --resource-group $ResourceGroup --query "[?name=='$WebAppName'].name" -o tsv)
if ($LASTEXITCODE -ne 0) {
    throw "Failed to query existing web apps in resource group."
}
if (-not $existing) {
    Invoke-Az -Args @("webapp", "create", "--resource-group", $ResourceGroup, "--plan", $PlanName, "--name", $WebAppName, "--container-image-name", $imageRef) -FailureMessage "Failed to create web app." | Out-Null
} else {
    Invoke-Az -Args @("webapp", "config", "container", "set", "--resource-group", $ResourceGroup, "--name", $WebAppName, "--container-image-name", $imageRef) -FailureMessage "Failed to update web app container image." | Out-Null
}

Write-Host "Configuring baseline app settings..." -ForegroundColor Cyan
Invoke-Az -Args @("webapp", "config", "appsettings", "set", "--resource-group", $ResourceGroup, "--name", $WebAppName, "--settings", "WEBSITES_PORT=8501", "SCM_DO_BUILD_DURING_DEPLOYMENT=false") -FailureMessage "Failed to apply baseline app settings." | Out-Null

Write-Host "Applying runtime settings..." -ForegroundColor Cyan
Invoke-Az -Args @("webapp", "config", "set", "--resource-group", $ResourceGroup, "--name", $WebAppName, "--always-on", "true", "--generic-configurations", '{"healthCheckPath":"/_stcore/health"}') -FailureMessage "Failed to configure runtime settings." | Out-Null

if (-not $SkipEnvImport) {
    Write-Host "Importing settings from env file..." -ForegroundColor Cyan
    $envPairs = Load-EnvSettings -Path $EnvFile
    if ($envPairs.Count -gt 0) {
        Invoke-Az -Args @("webapp", "config", "appsettings", "set", "--resource-group", $ResourceGroup, "--name", $WebAppName, "--settings") + $envPairs -FailureMessage "Failed to import environment settings." | Out-Null
    } else {
        Write-Host "No app settings imported from env file." -ForegroundColor Yellow
    }
}

Write-Host "Restarting web app..." -ForegroundColor Cyan
Invoke-Az -Args @("webapp", "restart", "--resource-group", $ResourceGroup, "--name", $WebAppName) -FailureMessage "Failed to restart web app." | Out-Null

$url = "https://$WebAppName.azurewebsites.net"
Write-Host ""
Write-Host "Deployment completed." -ForegroundColor Green
Write-Host "App URL: $url" -ForegroundColor Green
Write-Host ""
Write-Host "Next checks:" -ForegroundColor Yellow
Write-Host "1) Browse $url"
Write-Host "2) Confirm upload and requirement generation flows"
Write-Host "3) Set OPENAI_API_KEY in App Settings or Key Vault reference"
