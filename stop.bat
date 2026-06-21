@echo off
REM Stop git-github-mcp fleet ports
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop.ps1"
if errorlevel 1 pause

