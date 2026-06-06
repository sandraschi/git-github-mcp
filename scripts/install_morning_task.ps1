param(
    [string]$Time = "07:00",
    [string]$FleetFile = "",
    [string]$Deliver = "file,aiwatcher",
    [int]$StaleDays = 7,
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$TaskName = "GitHub-Fleet-Morning-Digest"
$RepoRoot = "D:\Dev\repos\git-github-mcp"
$Runner = Join-Path $RepoRoot "scripts\run_morning_digest.ps1"

if ($Remove) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Removed scheduled task: $TaskName" -ForegroundColor Yellow
    exit 0
}

if (-not (Test-Path $Runner)) {
    Write-Host "Missing runner: $Runner" -ForegroundColor Red
    exit 1
}

$argList = "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`" -StaleDays $StaleDays -Deliver `"$Deliver`""
if ($FleetFile) {
    $argList += " -FleetFile `"$FleetFile`""
}

$Action = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument $argList -WorkingDirectory $RepoRoot
$Trigger = New-ScheduledTaskTrigger -Daily -At $Time
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null

Write-Host "Installed daily task '$TaskName' at $Time" -ForegroundColor Green
Write-Host "  Runner: $Runner" -ForegroundColor Gray
Write-Host "  Deliver: $Deliver" -ForegroundColor Gray
Write-Host "  Fleet file: $(if ($FleetFile) { $FleetFile } else { 'config/fleet-repos.txt or default' })" -ForegroundColor Gray
Write-Host ""
Write-Host "Test now: pwsh -File `"$Runner`"" -ForegroundColor Cyan
Write-Host "Remove:   pwsh -File `"$PSCommandPath`" -Remove" -ForegroundColor Gray
