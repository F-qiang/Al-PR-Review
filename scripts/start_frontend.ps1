$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $ProjectRoot "frontend"

Set-Location $FrontendDir

if (-not (Test-Path "node_modules")) {
  Write-Host "node_modules not found, installing frontend dependencies..." -ForegroundColor Yellow
  npm install
}

Write-Host "Starting frontend at http://localhost:3000" -ForegroundColor Green
npm run dev
