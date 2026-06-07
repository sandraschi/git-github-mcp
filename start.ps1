param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser
)

$ScriptRoot = Split-Path -Parent $PSCommandPath
$WebRoot = Join-Path $ScriptRoot "web"
$BackendPort = 10702
$FrontendPort = 10703

. (Join-Path $ScriptRoot "scripts\FleetWebStart.ps1")

$FleetStartPath = Join-Path $ScriptRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath
$FleetStart = Initialize-FleetStartMode @PSBoundParameters
Enter-FleetHeadlessConsole -Headless:$Headless -BackendOnly:$BackendOnly

Write-Host "Starting git-github-mcp (fleet SOTA)..." -ForegroundColor Cyan
Write-Host "Frontend $FrontendPort | Backend $BackendPort | MCP /mcp" -ForegroundColor Gray

Stop-FleetPortSquatters -Ports @($BackendPort, $FrontendPort) -Label "git-github-mcp"

if (-not (Assert-FleetPortsAvailable -Ports @($BackendPort, $FrontendPort) -Label "git-github-mcp")) { exit 1 }

$uvExe = Require-FleetCommand -Cmd "uv" -WingetId "Astral.uv" -Label "uv"
$npmExe = Require-FleetCommand -Cmd "npm" -WingetId "OpenJS.NodeJS.LTS" -Label "npm"
Require-FleetCommand -Cmd "node" -WingetId "OpenJS.NodeJS.LTS" -Label "node" | Out-Null

if ($FleetStart.RunBackend) {
    Ensure-GitGithubPythonDeps -RepoRoot $ScriptRoot -UvExe $uvExe
    Start-GitGithubBackendWindow -RepoRoot $ScriptRoot -UvExe $uvExe
    if (-not (Wait-GitGithubBackend -BackendPort $BackendPort)) { exit 1 }
}

if (-not $FleetStart.RunFrontend) { return }

Ensure-GitGithubFrontendDeps -WebRoot $WebRoot -NpmExe $npmExe

$frontendUrl = "http://127.0.0.1:$FrontendPort/"
if (-not $FleetStart.SkipBrowser) {
    Start-GitGithubBrowserWhenReady -FrontendUrl $frontendUrl -OpenPath "/breakfast"
}

Set-Location $WebRoot
Write-Host "Starting Vite on $FrontendPort ..." -ForegroundColor Green
Write-Host "UI: http://127.0.0.1:$FrontendPort/breakfast" -ForegroundColor Gray
& $npmExe run dev -- --port $FrontendPort --host 127.0.0.1 --strictPort
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Vite exited with code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}


