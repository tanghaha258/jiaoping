param(
    [string]$DatabasePath = "",
    [string]$BackupDir = "backups"
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

if ([string]::IsNullOrWhiteSpace($DatabasePath)) {
    $DatabasePath = Get-DatabasePathFromEnv
}

if ([string]::IsNullOrWhiteSpace($DatabasePath)) {
    $DatabasePath = Join-Path $BackendDir "app.db"
}

$resolvedDatabase = Resolve-ProjectPath -PathValue $DatabasePath -BaseDir $Root
if (-not (Test-Path -LiteralPath $resolvedDatabase)) {
    throw "SQLite database not found: $resolvedDatabase"
}

$resolvedBackupDir = Resolve-ProjectPath -PathValue $BackupDir -BaseDir $Root
New-Item -ItemType Directory -Path $resolvedBackupDir -Force | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$sourceName = [System.IO.Path]::GetFileNameWithoutExtension($resolvedDatabase)
$target = Join-Path $resolvedBackupDir "$sourceName-$timestamp.db"

Copy-Item -LiteralPath $resolvedDatabase -Destination $target -Force

Write-Host "SQLite backup created: $target"
