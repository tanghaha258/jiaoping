param(
    [Parameter(Mandatory = $true)][string]$BackupPath,
    [string]$DatabasePath = "",
    [switch]$SkipSafetyBackup
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"

function Resolve-ProjectPath {
    param(
        [Parameter(Mandatory = $true)][string]$PathValue,
        [Parameter(Mandatory = $true)][string]$BaseDir
    )

    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }

    return [System.IO.Path]::GetFullPath((Join-Path $BaseDir $PathValue))
}

function Get-DatabasePathFromEnv {
    $envPath = Join-Path $BackendDir ".env"
    if (-not (Test-Path -LiteralPath $envPath)) {
        return ""
    }

    $line = Get-Content -LiteralPath $envPath |
        Where-Object { $_ -match "^\s*DATABASE_URL\s*=" } |
        Select-Object -First 1
    if (-not $line) {
        return ""
    }

    $url = ($line -replace "^\s*DATABASE_URL\s*=\s*", "").Trim().Trim('"').Trim("'")
    if ($url -notmatch "^sqlite") {
        return ""
    }

    $raw = $url -replace "^sqlite(\+aiosqlite)?:///", ""
    if ([string]::IsNullOrWhiteSpace($raw) -or $raw -eq ":memory:") {
        return ""
    }

    return (Resolve-ProjectPath -PathValue $raw -BaseDir $BackendDir)
}

$resolvedBackup = Resolve-ProjectPath -PathValue $BackupPath -BaseDir $Root
if (-not (Test-Path -LiteralPath $resolvedBackup)) {
    throw "SQLite backup not found: $resolvedBackup"
}

if ([string]::IsNullOrWhiteSpace($DatabasePath)) {
    $DatabasePath = Get-DatabasePathFromEnv
}

if ([string]::IsNullOrWhiteSpace($DatabasePath)) {
    $DatabasePath = Join-Path $BackendDir "app.db"
}

$resolvedDatabase = Resolve-ProjectPath -PathValue $DatabasePath -BaseDir $Root
$targetDir = Split-Path -Parent $resolvedDatabase
New-Item -ItemType Directory -Path $targetDir -Force | Out-Null

if ((Test-Path -LiteralPath $resolvedDatabase) -and -not $SkipSafetyBackup) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $sourceName = [System.IO.Path]::GetFileNameWithoutExtension($resolvedDatabase)
    $safetyBackup = Join-Path $targetDir "$sourceName.pre-restore-$timestamp.db"
    Copy-Item -LiteralPath $resolvedDatabase -Destination $safetyBackup -Force
    Write-Host "Pre-restore safety backup created: $safetyBackup"
}

Copy-Item -LiteralPath $resolvedBackup -Destination $resolvedDatabase -Force

Write-Host "SQLite database restored from: $resolvedBackup"
Write-Host "SQLite database target: $resolvedDatabase"
