# Development Setup

## Tools required

Install all of these before continuing (Windows via winget):

```powershell
winget install astral-sh.uv --accept-source-agreements --accept-package-agreements
winget install Git.Git --accept-source-agreements --accept-package-agreements
winget install GitHub.cli --accept-source-agreements --accept-package-agreements
winget install OpenJS.NodeJS --accept-source-agreements --accept-package-agreements
winget install Casey.Just --accept-source-agreements --accept-package-agreements
# Close and reopen PowerShell, then verify:
uv --version; git --version; gh --version; node --version; just --version
```

macOS: `brew install uv git gh node just`.

## Setup

```powershell
git clone https://github.com/sandraschi/git-github-mcp
cd git-github-mcp
just bootstrap   # uv sync --group dev + pre-commit install + web npm install
```

`just bootstrap` installs the pre-commit hook (Ruff + Biome + whitespace).
It runs automatically on every `git commit`.

## Common tasks

| Command | What it does |
|---------|--------------|
| `just ci` | Full local gate — **must be green before push** (ruff, pyright, pytest, advisory ty/pip-audit, `tsc`, biome) |
| `just lint` | `ruff check` + `biome ci` (no fixes) |
| `just fix` | `ruff --fix` + `ruff format` + `biome check --write` |
| `just e2e-install` / `just e2e` | Playwright chromium + smoke suite (needs backend on `:10713`, frontend on `:10714` — Playwright starts the backend itself via `webServer`) |
| `just check-sec` / `just audit-deps` | bandit / safety audits |
| `just mcpb-pack` | Claude Desktop `.mcpb` bundle |
| `just build-native` | Tauri NSIS installer (needs VS Build Tools + Rust) |
| `uv run pytest -q tests/` | Python tests directly |
| `uv run pyright src` | Type gate (blocking in CI — keep at zero) |

There is no `just serve` / `just dev`. Run the stack with `.\start.ps1`
(`-BackendOnly`, `-NoBrowser` switches) or `start.bat`.

## Ports

Backend `10713` · frontend `10714` (see `WEBAPP_PORTS.md` in
mcp-central-docs — never invent ports). `start.ps1` clears the port before
binding.

## Code standards

- Python: Ruff 0.16 (`[tool.ruff.lint] select` in `pyproject.toml`), `ruff format`.
- Web: Biome (`npm run biome:ci`), `tsc -b` via `npm run check`.
- Types: `pyright src/` is blocking — fix, don't suppress.
- Fleet-wide rules: `mcp-central-docs/standards/` (agent protocols, tool
  design, packaging). Conventional commits (`fix(scope): …`, `docs: …`,
  `ci: …`, `feat: …`).
