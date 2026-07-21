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

function Assert-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found. Install it and retry."
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

Assert-Command -Name "az"

az account show 1>$null
if ($LASTEXITCODE -ne 0) {
    throw "Azure CLI is not logged in. Run 'az login' and retry."
}

Set-Location $PSScriptRoot

Write-Host "Setting subscription..." -ForegroundColor Cyan
az account set --subscription $SubscriptionId

Write-Host "Ensuring resource group..." -ForegroundColor Cyan
az group create --name $ResourceGroup --location $Location 1>$null

Write-Host "Ensuring App Service plan..." -ForegroundColor Cyan
az appservice plan create --name $PlanName --resource-group $ResourceGroup --location $Location --is-linux --sku B1 1>$null

Write-Host "Ensuring Azure Container Registry..." -ForegroundColor Cyan
az acr create --name $AcrName --resource-group $ResourceGroup --location $Location --sku Basic --admin-enabled true 1>$null

$imageRef = "${AcrName}.azurecr.io/${ImageName}:${ImageTag}"

Write-Host "Building and pushing container image to ACR..." -ForegroundColor Cyan
az acr build --registry $AcrName --image "${ImageName}:${ImageTag}" .

Write-Host "Ensuring web app..." -ForegroundColor Cyan
$existing = az webapp list --resource-group $ResourceGroup --query "[?name=='$WebAppName'].name" -o tsv
if (-not $existing) {
    az webapp create --resource-group $ResourceGroup --plan $PlanName --name $WebAppName --deployment-container-image-name $imageRef 1>$null
} else {
    az webapp config container set --resource-group $ResourceGroup --name $WebAppName --container-image-name $imageRef 1>$null
}

Write-Host "Configuring baseline app settings..." -ForegroundColor Cyan
az webapp config appsettings set --resource-group $ResourceGroup --name $WebAppName --settings WEBSITES_PORT=8501 SCM_DO_BUILD_DURING_DEPLOYMENT=false 1>$null

Write-Host "Applying runtime settings..." -ForegroundColor Cyan
az webapp config set --resource-group $ResourceGroup --name $WebAppName --always-on true --health-check-path "/_stcore/health" 1>$null

if (-not $SkipEnvImport) {
    Write-Host "Importing settings from env file..." -ForegroundColor Cyan
    $envPairs = Load-EnvSettings -Path $EnvFile
    if ($envPairs.Count -gt 0) {
        az webapp config appsettings set --resource-group $ResourceGroup --name $WebAppName --settings $envPairs 1>$null
    } else {
        Write-Host "No app settings imported from env file." -ForegroundColor Yellow
    }
}

Write-Host "Restarting web app..." -ForegroundColor Cyan
az webapp restart --resource-group $ResourceGroup --name $WebAppName 1>$null

$url = "https://$WebAppName.azurewebsites.net"
Write-Host ""
Write-Host "Deployment completed." -ForegroundColor Green
Write-Host "App URL: $url" -ForegroundColor Green
Write-Host ""
Write-Host "Next checks:" -ForegroundColor Yellow
Write-Host "1) Browse $url"
Write-Host "2) Confirm upload and requirement generation flows"
Write-Host "3) Set OPENAI_API_KEY in App Settings or Key Vault reference"
