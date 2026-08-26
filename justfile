set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]
import 'scripts/just/fleet.just'

# --- Dashboard ---

# Open the interactive recipe dashboard in the browser
default:
    @just --list

bootstrap:
    uv sync --group dev
    uv run pre-commit install
    Set-Location '{{justfile_directory()}}\web'; npm ci; if ($LASTEXITCODE -ne 0) { npm install }
    Write-Host "Pre-commit hooks installed." -ForegroundColor Green

# --- Quality ---

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .
    Set-Location '{{justfile_directory()}}\web'
    npx @biomejs/biome ci .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .
    Set-Location '{{justfile_directory()}}\web'
    npx @biomejs/biome check --write .

# --- Hardening ---

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check

# --- MCPB  Claude Desktop bundle ---

# --- Tauri NSIS ---

# Build the Tauri NSIS desktop installer (full pipeline: frontend -> Rust -> NSIS)
build-native:
	$env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
	$vcvars = "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
	$envOutput = cmd /c "`"$vcvars`" > nul & set" | Where-Object { $_ -match '^(INCLUDE|LIB|LIBPATH|VCToolsVersion|WindowsSdkDir|UniversalCRTSdkDir|UCRTVersion)=' }
	foreach ($line in $envOutput) { $parts = $line.Split('=', 2); Set-Item -Path "env:$($parts[0])" -Value $parts[1] -ErrorAction SilentlyContinue }
	Set-Location '{{justfile_directory()}}\native'
	pwsh -NoProfile -File '{{justfile_directory()}}\native\build.ps1'

# --- Playwright E2E ---

# Install Playwright browsers (one-time)
e2e-install:
    Set-Location '{{justfile_directory()}}\web'
    npx playwright install chromium

# Run Playwright E2E smoke tests (start backend first: just serve)
e2e:
    Set-Location '{{justfile_directory()}}\web'
    npx playwright test

# Bootstrap: install dev deps + pre-commit hook
