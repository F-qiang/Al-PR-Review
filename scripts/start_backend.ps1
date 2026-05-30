$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"

Set-Location $BackendDir

if (-not (Test-Path ".env")) {
  Write-Host "未检测到 backend/.env，正在从 .env.example 创建..." -ForegroundColor Yellow
  Copy-Item ".env.example" ".env"
  Write-Host "请先编辑 backend/.env 并填写 LLM_API_KEY，然后重新运行本脚本。" -ForegroundColor Yellow
  exit 1
}

Write-Host "启动后端：http://127.0.0.1:8000" -ForegroundColor Green
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
