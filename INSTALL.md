# Installation — git-github-mcp

## Prerequisites

| Tool | Required for | Install |
|---|---|---|
| **git** | all local git operations | [git-scm.com](https://git-scm.com) |
| **gh CLI** | all `github_ops` calls | [cli.github.com](https://cli.github.com) |
| **Python 3.12+** + **uv** | Options B, C, and web app | [python.org](https://python.org) · [astral.sh/uv](https://docs.astral.sh/uv/) |
| **Node.js 20+** | web app only | [nodejs.org](https://nodejs.org) |

After installing gh CLI, authenticate once:
```powershell
gh auth login
```

---

## Claude Desktop — Option A: Drag-and-drop .mcpb (recommended)

1. Download `git-github-mcp.mcpb` from the [Releases page](https://github.com/sandraschi/git-github-mcp/releases/latest)
2. Open Claude Desktop
3. Drag the `.mcpb` file into the Claude Desktop window
4. Accept the install prompt

Done. No Python, uv, or git required on your end — Claude Desktop manages the runtime.

---

## Claude Desktop — Option B: mcpb CLI

> **Note:** `mcpb` is NOT on PyPI — `uvx mcpb` will fail. Install the mcpb CLI
> separately per [Anthropic's mcpb documentation](https://docs.anthropic.com/mcpb).

```powershell
mcpb install https://github.com/sandraschi/git-github-mcp/releases/latest/download/git-github-mcp.mcpb
```

---

## Claude Desktop — Option C: Manual config

Clone and install dependencies:

```powershell
git clone https://github.com/sandraschi/git-github-mcp
cd git-github-mcp
uv sync
```

Edit `%APPDATA%\Claude\claude_desktop_config.json` and add:

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

> **What starts:** the MCP stdio listener (for Claude Desktop) plus a FastAPI HTTP bridge
> on port 10702. The HTTP bridge is always active — see [HTTP bridge endpoints](#http-bridge-endpoints) below.

---

## Web App Mode

The repo includes a React frontend (Vite, port 10703) that talks to the FastAPI backend
(port 10702). This is the recommended way to use git-github-mcp outside of Claude Desktop.

### First-time setup

Install frontend dependencies:

```powershell
cd web
npm install
cd ..
```

### Starting the stack

From the repo root, double-click `start.bat` or run:

```powershell
.\start.ps1
```

Alternatively from the `web/` subdirectory:

```powershell
.\web\start.bat
```

The script:
1. Kills any process holding ports 10702 and 10703
2. Starts the backend (`uv run python -m git_github_mcp --http`) — MCP HTTP transport at `http://127.0.0.1:10702/mcp`, REST API at `http://127.0.0.1:10702/api/*`
3. Waits up to 60 s for the backend health check at `http://127.0.0.1:10702/health`
4. Starts the Vite dev server on port 10703
5. Opens `http://127.0.0.1:10703` in your browser

### start.ps1 switches

| Switch | Effect |
|---|---|
| `-BackendOnly` | Skip the Vite frontend — backend only |
| `-NoBrowser` | Don't auto-open the browser |
| `-Headless` | Alias for `-NoBrowser` |

### Starting backend only (manual)

```powershell
cd git-github-mcp
$env:MCP_TRANSPORT = "http"
uv run git-github-mcp
```

### Starting frontend only (assumes backend is already up)

```powershell
cd git-github-mcp\web
npx vite --port 10703 --host
```

---

## HTTP bridge endpoints

The FastAPI bridge starts automatically in all modes (Claude Desktop stdio, HTTP, or web app):

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Liveness check |
| `/api/status` | GET | git and gh CLI versions + auth state |
| `/api/tools` | GET | Tool manifest |
| `/api/git` | POST | Direct git operations (body: `{"operation": "status", ...}`) |
| `/api/github` | POST | Direct GitHub operations |
| `/api/discovery` | POST | Preset GitHub discovery chains |
| `/mcp` | — | MCP HTTP transport (HTTP mode only) |

---

## GitHub token

`github_ops` uses gh CLI auth by default (`gh auth login`). To use a token instead:

Add `GH_TOKEN` to the `env` block in `claude_desktop_config.json`, or set it before
starting the web app:

```powershell
$env:GH_TOKEN = "ghp_your_token_here"
.\start.ps1
```

`GH_TOKEN` takes precedence over interactive gh auth.

---

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` \| `http` \| `sse` |
| `MCP_HOST` | `127.0.0.1` | Bind address for HTTP/SSE |
| `MCP_PORT` | `10702` | MCP HTTP port |
| `MCP_PATH` | `/mcp` | MCP HTTP endpoint path |
| `WEB_PORT` | `10702` | FastAPI bridge port (same as MCP_PORT by default) |
| `GH_TOKEN` | — | GitHub token (overrides gh CLI auth) |
| `PYTHONUNBUFFERED` | — | Set to `1` in Claude Desktop config for clean logs |

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `github_ops` — "gh CLI not found" | Install [gh CLI](https://cli.github.com) and ensure it's on `PATH` |
| `github_ops` — "not logged in" | `gh auth login` or set `GH_TOKEN` |
| `git_core` times out after 25 s | git subprocess is hanging (Windows Job Object issue under Electron). Use the REST API at `http://127.0.0.1:10702/api/git` as fallback |
| Backend health check never returns 200 | Run `uv sync` first; check `uv run git-github-mcp` directly in a terminal |
| Port 10702 already in use | `Get-NetTCPConnection -LocalPort 10702 | Stop-Process -Id {$_.OwningProcess}` or set `WEB_PORT` |
| Port 10703 already in use | Change `--port` in `start.ps1` and in `web/vite.config.ts` |
| `uvx mcpb install` fails | mcpb is not on PyPI — use Option A (drag-and-drop) instead |
| `uv` not found | [astral.sh/uv install guide](https://docs.astral.sh/uv/getting-started/installation/) |
| `npx vite` not found | Install Node.js 20+ from [nodejs.org](https://nodejs.org) |

---

*See [README.md](README.md) for tool reference and feature overview.*
