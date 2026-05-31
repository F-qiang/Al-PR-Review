$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $ProjectRoot "frontend"
$frontendPort = 3000

Set-Location $FrontendDir

if (-not (Test-Path "node_modules")) {
  Write-Host "node_modules not found, installing frontend dependencies..." -ForegroundColor Yellow
  npm install
}

if (Get-NetTCPConnection -LocalPort $frontendPort -State Listen -ErrorAction SilentlyContinue) {
  Write-Host "Port $frontendPort is already in use. Stop the existing frontend process first." -ForegroundColor Red
  exit 1
}

Write-Host "Starting frontend at http://localhost:$frontendPort" -ForegroundColor Green
npm run dev
