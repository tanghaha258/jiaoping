param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"

Write-Host "Starting local trial runtime..."

$backendArgs = "-NoExit", "-Command", "cd `"$BackendDir`"; python -m uvicorn app.main:app --host 127.0.0.1 --port $BackendPort"
$frontendArgs = "-NoExit", "-Command", "cd `"$FrontendDir`"; npm run dev -- --host 127.0.0.1 --port $FrontendPort"

$backend = Start-Process powershell -ArgumentList $backendArgs -PassThru -WindowStyle Minimized
$frontend = Start-Process powershell -ArgumentList $frontendArgs -PassThru -WindowStyle Minimized

Write-Host "Backend PID: $($backend.Id)  URL: http://127.0.0.1:$BackendPort/api/v1/health"
Write-Host "Frontend PID: $($frontend.Id) URL: http://127.0.0.1:$FrontendPort"
Write-Host "Run smoke check: python scripts/smoke_deploy.py"
