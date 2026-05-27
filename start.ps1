param([switch]$Headless, [switch]$BackendOnly, [switch]$NoBrowser)
$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $PSCommandPath
$BackendPort = 10702
$FrontendPort = 10703

Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

$BackendJob = Start-Job -Name "backend" -ScriptBlock {
    param($Root)
    Set-Location $Root
    $env:MCP_TRANSPORT = "http"
    uv run git-github-mcp
} -ArgumentList $ScriptRoot

Write-Host "Waiting for backend on :$BackendPort ..." -ForegroundColor Cyan
for ($i = 0; $i -lt 60; $i++) {
    try { $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
          if ($r.StatusCode -eq 200) { Write-Host "Backend ready" -ForegroundColor Green; break } } catch {}
    Start-Sleep 1
}

if (-not $BackendOnly) {
    $WebRoot = Join-Path $ScriptRoot "web"
    Write-Host "Starting frontend on :$FrontendPort ..." -ForegroundColor Cyan
    Start-Process -NoNewWindow -FilePath "npx" -ArgumentList "vite --port $FrontendPort --host" -WorkingDirectory $WebRoot
}

if (-not $NoBrowser) {
    Start-Sleep 2
    Start-Process "http://127.0.0.1:$FrontendPort"
}

while ($true) {
    if ($BackendJob.State -eq "Completed" -or $BackendJob.State -eq "Failed") {
        Receive-Job $BackendJob; break
    }
    Start-Sleep 2
}
