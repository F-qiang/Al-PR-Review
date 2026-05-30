$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $ProjectRoot "frontend"

Set-Location $FrontendDir

if (-not (Test-Path "node_modules")) {
  Write-Host "未检测到 node_modules，正在安装前端依赖..." -ForegroundColor Yellow
  npm install
}

Write-Host "启动前端：http://localhost:3000" -ForegroundColor Green
npm run dev
