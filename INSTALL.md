# Installing git-github-mcp

Git (local) and GitHub operations for Claude Desktop and Claude Code.

---

## Prerequisites

Install these if you don't have them already. Windows commands use
[winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/)
(built into Windows 10 1809+ / Windows 11):

| Tool | Required for | Windows | macOS |
|------|-------------|---------|-------|
| **Claude Desktop** | all options | [claude.ai/download](https://claude.ai/download) | same |
| **git** | local git operations (all options) | `winget install Git.Git` | `brew install git` |
| **gh CLI** | GitHub operations (all options) | `winget install GitHub.cli` | `brew install gh` |
| **uv** | Options C and D | `winget install astral-sh.uv` | `brew install uv` |
| **Node.js** | Option B only | `winget install OpenJS.NodeJS` | `brew install node` |

> **Windows:** After any winget install, **close and reopen PowerShell** so PATH updates apply.  
> **macOS:** use `brew install git gh uv node` equivalents.

After installing gh CLI, authenticate once:

```powershell
gh auth login
```

---

## Option A — Drag and Drop (Recommended)

No Python or uv required. Claude Desktop manages the runtime.

1. Go to [Releases](https://github.com/sandraschi/git-github-mcp/releases/latest)
2. Download `git-github-mcp-*.mcpb`
3. Open Claude Desktop
4. Drag the `.mcpb` file onto the Claude Desktop window and accept the install prompt

**Pass criteria:** server appears in the MCP list with no terminal steps.

---

## Option B — mcpb CLI

`mcpb` is **not** on PyPI — `uvx mcpb` will fail. Requires Node.js:

```powershell
winget install OpenJS.NodeJS --accept-source-agreements --accept-package-agreements
# Close and reopen terminal, then:
npx @anthropic-ai/mcpb install https://github.com/sandraschi/git-github-mcp
```

Restart Claude Desktop after install completes.

---

## Option C — Manual Configuration

```powershell
winget install astral-sh.uv --accept-source-agreements --accept-package-agreements
winget install Git.Git --accept-source-agreements --accept-package-agreements
# Close and reopen terminal

git clone https://github.com/sandraschi/git-github-mcp
cd git-github-mcp
uv sync --all-extras
```

Edit Claude Desktop config:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "git-github-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\path\\to\\git-github-mcp",
        "run",
        "git-github-mcp",
        "--stdio"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

Replace `C:\\path\\to\\git-github-mcp` with your actual clone path. Restart Claude Desktop.

> The server also starts a FastAPI HTTP bridge on port 10702. Always active — see
> [HTTP bridge endpoints](#http-bridge-endpoints) below.

---

## Option D — Web App Mode

React frontend (Vite, port 10703) + FastAPI backend (port 10702). Requires Option D setup.

```powershell
winget install Casey.Just --accept-source-agreements --accept-package-agreements
cd web && npm install && cd ..
.\start.ps1
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for full dev setup, lint, tests, and mcpb packaging.

| Switch | Effect |
|--------|--------|
| `-BackendOnly` | Skip Vite frontend |
| `-NoBrowser` | Don't auto-open browser |

---

## Verify Installation

In Claude Desktop, try:

> "What is the git status of my current repo?"

You should see a structured response from `git_core`. If you get "tool not found", restart
Claude Desktop and check that the server appears in Settings → MCP Servers.

---

## GitHub Token

`github_ops` uses gh CLI auth by default. To use a PAT instead, add to the `env` block:

```json
"env": {
  "PYTHONUNBUFFERED": "1",
  "GH_TOKEN": "ghp_your_token_here"
}
```

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` \| `http` \| `sse` |
| `MCP_HOST` | `127.0.0.1` | Bind address for HTTP/SSE |
| `MCP_PORT` | `10702` | MCP HTTP port |
| `MCP_PATH` | `/mcp` | MCP endpoint path |
| `GH_TOKEN` | — | GitHub token (overrides gh CLI auth) |
| `PYTHONUNBUFFERED` | — | Set to `1` in Claude Desktop config |

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for the full reference.

---

## HTTP Bridge Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Liveness check |
| `/api/status` | GET | git and gh CLI versions + auth state |
| `/api/tools` | GET | Tool manifest |
| `/api/git` | POST | Direct git operations |
| `/api/github` | POST | Direct GitHub operations |
| `/mcp` | — | MCP HTTP transport (HTTP mode only) |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `github_ops` — "gh CLI not found" | `winget install GitHub.cli` then `gh auth login` |
| `github_ops` — "not logged in" | `gh auth login` or set `GH_TOKEN` |
| `git_core` times out after 25 s | Windows Job Object issue under Electron — use `/api/git` REST fallback |
| Server not in Claude Desktop | Run `uv run git-github-mcp --stdio` directly to see error; check config path |
| Port 10702 already in use | `Get-NetTCPConnection -LocalPort 10702` then kill the owner |
| `uv` not found | `winget install astral-sh.uv`; reopen terminal |
| `uvx mcpb` fails | Expected — use Option A or `npx @anthropic-ai/mcpb` |

Full diagnostics: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) · [open an issue](https://github.com/sandraschi/git-github-mcp/issues)

---

*Feature overview: [README.md](README.md)*
