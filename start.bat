@echo off
setlocal
REM git-github-mcp — FastAPI+MCP 10713, Vite 10714
cd /d "%~dp0"

set "PATH=%PATH%;%LOCALAPPDATA%\Microsoft\WindowsApps"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
set "EC=%ERRORLEVEL%"
if %EC% NEQ 0 (
  echo Exit code: %EC%
  pause
)
endlocal & exit /b %EC%
