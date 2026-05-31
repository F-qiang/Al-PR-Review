$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$EnvFile = Join-Path $BackendDir ".env"

Set-Location $BackendDir

if (-not (Test-Path $EnvFile)) {
  Write-Host "backend/.env not found, copying from .env.example..." -ForegroundColor Yellow
  Copy-Item ".env.example" ".env"
  Write-Host "Please edit backend/.env and fill LLM_API_KEY, then run this script again." -ForegroundColor Yellow
  exit 1
}

$envLines = Get-Content $EnvFile
$llmKeyLine = $envLines | Where-Object { $_ -match '^LLM_API_KEY=' } | Select-Object -First 1
$dbLine = $envLines | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1

if ([string]::IsNullOrWhiteSpace($llmKeyLine) -or $llmKeyLine -eq 'LLM_API_KEY=') {
  Write-Host "LLM_API_KEY is empty. Please fill backend/.env first." -ForegroundColor Red
  exit 1
}

if ([string]::IsNullOrWhiteSpace($dbLine)) {
  Write-Host "DATABASE_URL is missing in backend/.env." -ForegroundColor Red
  exit 1
}

$backendPort = 8000
if (Get-NetTCPConnection -LocalPort $backendPort -State Listen -ErrorAction SilentlyContinue) {
  Write-Host "Port $backendPort is already in use. Stop the existing backend process first." -ForegroundColor Red
  exit 1
}

Write-Host "Starting backend at http://127.0.0.1:$backendPort" -ForegroundColor Green
python -m uvicorn app.main:app --host 127.0.0.1 --port $backendPort --reload
