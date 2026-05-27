$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Running backend tests..."
Set-Location $Root
Invoke-Checked { python -m pytest backend/tests -q }

Write-Host "Compiling backend..."
Invoke-Checked { python -m compileall backend\app }

Write-Host "Checking frontend text health..."
Invoke-Checked { python scripts\check_frontend_text_health.py }

Write-Host "Checking frontend route smoke..."
Invoke-Checked { python scripts\check_frontend_route_smoke.py }

Write-Host "Building frontend..."
Set-Location (Join-Path $Root "frontend")
Invoke-Checked { npm run build }

Set-Location $Root
Write-Host "Release checks completed."
