# git-github-mcp — Agent Guide

## Overview
FastMCP 3.2.0+ hardened substrate for Git (local) and GitHub (gh CLI)

## Entry Points
- `uv run git-github-mcp` → `git_github_mcp.__main__:main`

## Standards
- FastMCP 3.2+ portmanteau tool pattern — tools use `operation` enum param
- Responses: structured dicts with `success`, `message`, domain-specific fields
- Dual transport: stdio (Claude Desktop) + HTTP (`MCP_TRANSPORT=http`)
- See [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs) for fleet-wide coding standards

## Key Files
- `README.md` — full documentation
- `pyproject.toml` — build config and entry points
- `CLAUDE.md` — Claude Code context (if present)

Install docs: follow mcp-central-docs/standards/AGENT_INSTALL_REFERENCE.md

## Breakfast runner

```powershell
copy config\fleet-repos.example.txt config\fleet-repos.txt
uv run python scripts/run_morning_digest.py --deliver file,aiwatcher
.\scripts\install_morning_task.ps1
```

MCP: `fleet_morning_digest` · HTTP: `POST /api/morning-digest` · Web: `http://127.0.0.1:10703/breakfast`
