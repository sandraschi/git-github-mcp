$ProjectRoot = $PSScriptRoot

$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath

if (-not (Stop-FleetPortListeners -Ports @(10702, 10703) -Label "git-github-mcp")) { exit 1 }
