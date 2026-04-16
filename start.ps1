# git-github-mcp start script (SOTA v14.x Standard)
# Backend FastAPI on 10702, Frontend Vite on 10703

$BackendPort = 10702
$FrontendPort = 10703
$RepoRoot = $PSScriptRoot

Write-Host "git-github-mcp v0.4.1 [SOTA v14.x]" -ForegroundColor Green
Write-Host "  v1.20 Hardened CLI Safety: Enforced" -ForegroundColor Green
Write-Host "  High-Fidelity status parsing: Active" -ForegroundColor Green
Write-Host ""
Write-Host "  GitHub API features need the GitHub CLI logged in." -ForegroundColor Yellow
Write-Host "  If you have not yet: run  gh auth login  in a terminal, then  gh auth status" -ForegroundColor Yellow
Write-Host ""

# Kill zombies on both ports
foreach ($port in @($BackendPort, $FrontendPort)) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        $conn | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
        Write-Host "  Cleared port $port" -ForegroundColor Yellow
    }
}

Start-Sleep -Milliseconds 500

# Start FastAPI backend
Write-Host "  Starting backend on :$BackendPort ..." -ForegroundColor Cyan
$backendJob = Start-Process -FilePath "uv" `
    -ArgumentList "run git-github-mcp --http" `
    -WorkingDirectory $RepoRoot `
    -WindowStyle Minimized `
    -PassThru

Start-Sleep -Seconds 2

# Start Vite dev frontend
Write-Host "  Starting frontend on :$FrontendPort ..." -ForegroundColor Cyan
$frontendJob = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c npm run dev" `
    -WorkingDirectory (Join-Path $RepoRoot "web") `
    -WindowStyle Minimized `
    -PassThru

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "  Backend  http://localhost:$BackendPort/api/status" -ForegroundColor Green
Write-Host "  Frontend http://localhost:$FrontendPort" -ForegroundColor Green
Write-Host ""
Write-Host "  Press Ctrl+C to stop" -ForegroundColor Gray

# Last step: open webapp in default browser
Start-Process "http://localhost:$FrontendPort"

# Wait
try { Wait-Process -Id $frontendJob.Id } catch { }
