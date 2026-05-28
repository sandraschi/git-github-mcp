# git-github-mcp — Claude Code Guide

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
- `AGENTS.md` — OpenAI Codex agent context (if present)
