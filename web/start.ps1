# git-github-mcp start script
# Backend FastAPI on 10702, Frontend Vite on 10703

$BackendPort = 10702
$FrontendPort = 10703
$RepoRoot = $PSScriptRoot | Split-Path -Parent

Write-Host "git-github-mcp v0.2.0 startup" -ForegroundColor Green

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
    -ArgumentList "run --directory `"$RepoRoot`" git-github-mcp --http" `
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

# Open browser
Start-Process "http://localhost:$FrontendPort"

# Wait
try { Wait-Process -Id $frontendJob.Id } catch { }
