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
$exitCode = $LASTEXITCODE

# Mirror into the repo tree so opencode/Cursor/Antigravity/a fresh Claude session
# can find it by browsing D:\Dev\repos - %LOCALAPPDATA% is invisible to them.
if ($exitCode -eq 0) {
    $sourceDigest = Join-Path $env:LOCALAPPDATA "git-github-mcp\morning-digest.md"
    $mirrorDir = "D:\Dev\repos\mcp-central-docs\operations"
    if (Test-Path $sourceDigest) {
        New-Item -ItemType Directory -Force -Path $mirrorDir | Out-Null
        Copy-Item -LiteralPath $sourceDigest -Destination (Join-Path $mirrorDir "fleet-status.md") -Force
        Write-Host "[git-github-mcp] Mirrored digest to $mirrorDir\fleet-status.md" -ForegroundColor Gray
    }
}

exit $exitCode
