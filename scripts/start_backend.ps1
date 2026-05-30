$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"

Set-Location $BackendDir

if (-not (Test-Path ".env")) {
  Write-Host "backend/.env not found, copying from .env.example..." -ForegroundColor Yellow
  Copy-Item ".env.example" ".env"
  Write-Host "Please edit backend/.env and fill LLM_API_KEY, then run this script again." -ForegroundColor Yellow
  exit 1
}

Write-Host "Starting backend at http://127.0.0.1:8000" -ForegroundColor Green
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
