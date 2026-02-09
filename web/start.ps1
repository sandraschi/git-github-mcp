# Start Git GitHub Hub webapp (dev mode: Vite + FastAPI)
# Requires: npm install, gh auth login

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Start backend
$backend = Start-Process -FilePath "python" -ArgumentList "server.py" -PassThru -WindowStyle Hidden

# Wait for backend to be ready
Start-Sleep -Seconds 2

# Start Vite dev server
Write-Host "Backend on http://localhost:5180, Vite proxying /api"
Write-Host "Open http://localhost:5173"
npm run dev
