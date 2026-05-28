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

> After a winget install, close and reopen your terminal so the new tool is on PATH.

After installing gh CLI, authenticate once:

```powershell
gh auth login
```

---

## Option A — Drag and Drop (Recommended)

No Python or uv required. Claude Desktop manages the runtime.

1. Go to [Releases](https://github.com/sandraschi/git-github-mcp/releases/latest)
2. Download `git-github-mcp-{version}.mcpb`
3. Open Claude Desktop
4. Drag the `.mcpb` file onto the Claude Desktop window and accept the install prompt

Done.

---

## Option B — mcpb CLI

Requires Node.js (see Prerequisites above).

```powershell
npx @anthropic-ai/mcpb install https://github.com/sandraschi/git-github-mcp
```

> `uvx mcpb` will NOT work — mcpb is an npm package, not on PyPI.

---

## Option C — Manual Configuration

Requires uv and git (see Prerequisites above).

```powershell
git clone https://github.com/sandraschi/git-github-mcp
cd git-github-mcp
uv sync
```

Add to `claude_desktop_config.json`:

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
        "git-github-mcp"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

Replace `C:\\path\\to\\git-github-mcp` with your actual clone path. Restart Claude Desktop.

> The server starts a FastAPI HTTP bridge on port 10702 in addition to the MCP stdio
> listener. This is always active — see [HTTP bridge endpoints](#http-bridge-endpoints) below.

---

## Option D — Web App Mode

Includes a React frontend (Vite, port 10703) that talks to the FastAPI backend (port 10702).

```powershell
cd web
npm install
cd ..
.\start.ps1
```

`start.ps1` kills any process holding ports 10702/10703, starts the backend, waits for the
health check, then opens `http://127.0.0.1:10703` in your browser.

| Switch | Effect |
|--------|--------|
| `-BackendOnly` | Skip Vite frontend |
| `-NoBrowser` | Don't auto-open browser |

---

## Verify Installation

After installing, open Claude Desktop and type:

> "What is the git status of my current repo?"

You should see a structured response from `git_core`. If you get "tool not found", restart
Claude Desktop and check that the server appears in Settings → MCP Servers.

---

## GitHub Token

`github_ops` uses gh CLI auth by default. To use a PAT instead:

Add to the `env` block in `claude_desktop_config.json`:

```json
"env": {
  "PYTHONUNBUFFERED": "1",
  "GH_TOKEN": "ghp_your_token_here"
}
```

`GH_TOKEN` takes precedence over interactive gh auth.

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

---

## HTTP Bridge Endpoints

The FastAPI bridge starts automatically alongside the MCP server:

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
| Server not in Claude Desktop | Run `uv run git-github-mcp` directly in terminal to see error; check config path |
| Port 10702 already in use | `Get-NetTCPConnection -LocalPort 10702` then kill the owner |
| `uv` not found | `winget install astral-sh.uv` then reopen terminal |
| `npx mcpb` fails | Ensure Node.js is installed: `winget install OpenJS.NodeJS` |

For more: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) · [open an issue](https://github.com/sandraschi/git-github-mcp/issues)
