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

$central = Get-FleetCentralDocsPath -RepoRoot $ScriptRoot
if ($central) {
    . (Join-Path $central "standards\FleetStartMode.ps1")
    $FleetStart = Initialize-FleetStartMode @PSBoundParameters
    Enter-FleetHeadlessConsole -Headless:$Headless -BackendOnly:$BackendOnly
} else {
    $FleetStart = [pscustomobject]@{
        RunBackend  = -not $FrontendOnly
        RunFrontend = (-not $BackendOnly) -and (-not $Headless)
        SkipBrowser = $NoBrowser -or $Headless -or $BackendOnly
    }
}

Write-Host "Starting git-github-mcp (fleet SOTA)..." -ForegroundColor Cyan
Write-Host "Frontend $FrontendPort | Backend $BackendPort | MCP /mcp" -ForegroundColor Gray

Stop-FleetZombies -Ports @($BackendPort, $FrontendPort)

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
& $npmExe run dev -- --port $FrontendPort --host 127.0.0.1 --strictPort
