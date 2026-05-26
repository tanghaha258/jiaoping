$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "Running backend tests..."
Set-Location $Root
python -m pytest backend/tests -q

Write-Host "Compiling backend..."
python -m compileall backend\app

Write-Host "Checking frontend text health..."
python scripts\check_frontend_text_health.py

Write-Host "Checking frontend route smoke..."
python scripts\check_frontend_route_smoke.py

Write-Host "Building frontend..."
Set-Location (Join-Path $Root "frontend")
npm run build

Set-Location $Root
Write-Host "Release checks completed."
