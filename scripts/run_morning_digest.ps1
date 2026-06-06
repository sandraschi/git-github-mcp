param(
    [string]$FleetFile = "",
    [string]$Deliver = "file,aiwatcher",
    [int]$StaleDays = 7
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $RepoRoot

$args = @(
    "run", "python", "scripts/run_morning_digest.py",
    "--stale-days", $StaleDays,
    "--deliver", $Deliver
)
if ($FleetFile) {
    $args += @("--fleet-file", $FleetFile)
}

Write-Host "[git-github-mcp] Morning digest..." -ForegroundColor Cyan
uv @args
exit $LASTEXITCODE
