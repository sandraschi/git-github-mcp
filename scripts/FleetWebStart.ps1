# Shared fleet web launcher helpers for git-github-mcp (NAKED_PC + zombie kill).

function Get-FleetCentralDocsPath {
    param([string]$RepoRoot)
    $candidates = @(
        (Join-Path $RepoRoot "..\mcp-central-docs"),
        "D:\Dev\repos\mcp-central-docs"
    )
    foreach ($c in $candidates) {
        $resolved = Resolve-Path $c -ErrorAction SilentlyContinue
        if ($resolved -and (Test-Path (Join-Path $resolved "standards\FleetStartMode.ps1"))) {
            return $resolved.Path
        }
    }
    return $null
}

function Stop-FleetZombies {
    param(
        [Parameter(Mandatory)]
        [int[]]$Ports,
        [string]$Label = "git-github-mcp"
    )
    Write-Host "[$Label] Clearing port zombies: $($Ports -join ', ')" -ForegroundColor Yellow
    foreach ($pass in 1..2) {
        foreach ($port in ($Ports | Sort-Object -Unique)) {
            if ($port -le 0) { continue }
            $pids = @(Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
                Where-Object { $_.OwningProcess -gt 4 } |
                Select-Object -ExpandProperty OwningProcess -Unique)
            foreach ($procId in $pids) {
                try {
                    Write-Host "  pass $pass - stop PID $procId on port $port" -ForegroundColor DarkGray
                    Stop-Process -Id $procId -Force -ErrorAction Stop
                } catch {
                    Write-Host "  warning: could not stop PID $procId on port $port" -ForegroundColor Gray
                }
            }
        }
        if ($pass -eq 1) { Start-Sleep -Seconds 2 }
    }
    $still = @()
    foreach ($port in ($Ports | Sort-Object -Unique)) {
        if ($port -le 0) { continue }
        $n = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue).Count
        if ($n -gt 0) { $still += $port }
    }
    if ($still.Count -gt 0) {
        Write-Host "[$Label] WARNING: ports still listening: $($still -join ', ')" -ForegroundColor Red
    } else {
        Write-Host "[$Label] Ports clear." -ForegroundColor Green
    }
}

function Require-FleetCommand {
    param(
        [string]$Cmd,
        [string]$WingetId,
        [string]$Label
    )
    if (Get-Command $Cmd -ErrorAction SilentlyContinue) {
        Write-Host "  [ok] $Label" -ForegroundColor DarkGreen
        if ($Cmd -eq "npm") {
            $npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
            if ($npmCmd) { return $npmCmd.Source }
        }
        return (Get-Command $Cmd).Source
    }
    Write-Host "  [--] $Label not found - installing via winget ..." -ForegroundColor Yellow
    $wingetExe = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $wingetExe) {
        $candidates = @(
            "$env:LOCALAPPDATA\Microsoft\WindowsApps\winget.exe",
            "$env:PROGRAMFILES\WindowsApps\Microsoft.DesktopAppInstaller_*\winget.exe"
        )
        foreach ($c in $candidates) {
            $found = Get-Item $c -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found) { $wingetExe = $found.FullName; break }
        }
    } else {
        $wingetExe = $wingetExe.Source
    }
    if (-not $wingetExe) {
        Write-Host "ERROR: winget not found. Install $Label manually (id: $WingetId)" -ForegroundColor Red
        exit 1
    }
    & $wingetExe install --id $WingetId --silent --accept-source-agreements --accept-package-agreements
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH", "User")
    if (-not (Get-Command $Cmd -ErrorAction SilentlyContinue)) {
        Write-Host "Installed $Label but '$Cmd' not in PATH yet. Reopen PowerShell and retry." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "  [ok] $Label installed" -ForegroundColor Green
    if ($Cmd -eq "npm") {
        $npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
        if ($npmCmd) { return $npmCmd.Source }
    }
    return (Get-Command $Cmd).Source
}

function Test-ViteBinPresent {
    param([string]$WebRootPath)
    $bin = Join-Path $WebRootPath "node_modules\.bin"
    foreach ($name in @("vite", "vite.cmd", "vite.exe")) {
        if (Test-Path -LiteralPath (Join-Path $bin $name)) { return $true }
    }
    return (Test-Path -LiteralPath (Join-Path $WebRootPath "node_modules\vite\package.json"))
}

function Ensure-GitGithubPythonDeps {
    param([string]$RepoRoot, [string]$UvExe)
    Write-Host "Syncing Python deps (uv) ..." -ForegroundColor Cyan
    & $UvExe sync --project $RepoRoot --extra dev
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: uv sync failed." -ForegroundColor Red
        exit 1
    }
    & $UvExe run --project $RepoRoot python -c "import git_github_mcp.server; print('  [ok] import git_github_mcp.server')"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Python import check failed." -ForegroundColor Red
        exit 1
    }
}

function Ensure-GitGithubFrontendDeps {
    param([string]$WebRoot, [string]$NpmExe)
    if (-not (Test-Path $WebRoot)) {
        Write-Host "ERROR: web folder not found: $WebRoot" -ForegroundColor Red
        exit 1
    }
    Push-Location $WebRoot
    try {
        if (-not (Test-Path "node_modules")) {
            Write-Host "Installing npm dependencies ..." -ForegroundColor Cyan
            $npmCmd = if ($NpmExe -like "*.cmd") { $NpmExe } else { (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source }
            if (-not $npmCmd) { $npmCmd = $NpmExe }
            & $npmCmd install --prefer-offline
            if ($LASTEXITCODE -ne 0) {
                Write-Host "ERROR: npm install failed." -ForegroundColor Red
                exit 1
            }
        }
        if (-not (Test-ViteBinPresent -WebRootPath $WebRoot)) {
            Write-Host "ERROR: vite missing from node_modules. Delete node_modules and re-run." -ForegroundColor Red
            exit 1
        }
    } finally {
        Pop-Location
    }
}

function Wait-GitGithubBackend {
    param([int]$BackendPort, [int]$MaxWaitSec = 90)
    $healthUrl = "http://127.0.0.1:$BackendPort/health"
    Write-Host "Waiting for backend on :$BackendPort " -NoNewline -ForegroundColor Cyan
    for ($i = 0; $i -lt $MaxWaitSec; $i++) {
        try {
            $null = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            Write-Host ""
            Write-Host "Backend ready on $BackendPort" -ForegroundColor Green
            return $true
        } catch {
            if (($i % 5) -eq 0) { Write-Host "." -NoNewline -ForegroundColor Cyan }
            Start-Sleep -Seconds 1
        }
    }
    Write-Host ""
    Write-Host "ERROR: backend health timed out after ${MaxWaitSec}s on $BackendPort" -ForegroundColor Red
    Write-Host "Check the backend PowerShell window (gh auth, uv sync)." -ForegroundColor Yellow
    return $false
}

function Start-GitGithubBackendWindow {
    param([string]$RepoRoot, [string]$UvExe)
    $backendCmd = @"
Set-Location '$RepoRoot'
Remove-Item Env:MCP_TRANSPORT -ErrorAction SilentlyContinue
& '$UvExe' run --project '$RepoRoot' git-github-mcp
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WorkingDirectory $RepoRoot -WindowStyle Normal
}

function Start-GitGithubBrowserWhenReady {
    param([string]$FrontendUrl, [string]$OpenPath = "/")
    $target = ($FrontendUrl.TrimEnd('/')) + $OpenPath
    $pollAndOpen = @"
for (`$i = 0; `$i -lt 60; `$i++) {
    try {
        `$null = Invoke-WebRequest -Uri '$FrontendUrl' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        Start-Process '$target'
        exit
    } catch { Start-Sleep -Seconds 1 }
}
"@
    Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $pollAndOpen
}
