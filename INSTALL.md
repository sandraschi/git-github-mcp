# Installation — git-github-mcp

## Prerequisites

All options require these to be on your `PATH`:

| Tool | Required for | Install |
|---|---|---|
| **git** | all local git operations | [git-scm.com](https://git-scm.com) |
| **gh CLI** | all `github_ops` calls | [cli.github.com](https://cli.github.com) |
| **Python 3.12+** + **uv** | Option B & C | [python.org](https://python.org), [astral.sh/uv](https://docs.astral.sh/uv/) |

After installing gh CLI, authenticate once:
```powershell
gh auth login
```

---

## Option A — Drag-and-drop .mcpb (recommended)

1. Download `git-github-mcp.mcpb` from the [Releases page](https://github.com/sandraschi/git-github-mcp/releases/latest)
2. Open Claude Desktop
3. Drag the `.mcpb` file into the Claude Desktop window
4. Accept the install prompt

Done. Claude Desktop handles the rest.

> **Note:** The `.mcpb` format bundles the server and all metadata. No Python or uv required for this path — Claude Desktop manages the runtime.

---

## Option B — mcpb CLI

> **Prerequisite:** `mcpb` is NOT on PyPI — `uvx mcpb` will fail. Install the mcpb CLI
> separately following [Anthropic's mcpb documentation](https://docs.anthropic.com/mcpb).

```powershell
mcpb install https://github.com/sandraschi/git-github-mcp/releases/latest/download/git-github-mcp.mcpb
```

---

## Option C — Manual config (Claude Desktop)

Clone the repo and add to `claude_desktop_config.json`:

```powershell
git clone https://github.com/sandraschi/git-github-mcp
cd git-github-mcp
uv sync
```

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

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

Replace `C:\\path\\to\\git-github-mcp` with the actual clone path.

Restart Claude Desktop after editing the config.

---

## GitHub token (optional)

`github_ops` uses the `gh` CLI auth by default (`gh auth login`). If you prefer a token:

```json
"env": {
  "PYTHONUNBUFFERED": "1",
  "GH_TOKEN": "ghp_your_token_here"
}
```

`GH_TOKEN` takes precedence over interactive gh auth.

---

## Web bridge

When the server starts, it also launches a local HTTP bridge at `http://127.0.0.1:10702`.
Endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness check |
| `GET /api/status` | git and gh CLI status |
| `GET /api/tools` | Tool manifest |
| `POST /api/git` | Direct git operations |
| `POST /api/github` | Direct GitHub operations |
| `POST /mcp` | MCP HTTP transport (alternate to stdio) |

The web bridge starts automatically alongside the stdio MCP listener — no extra config needed.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `github_ops` returns "gh CLI not found" | Install [gh CLI](https://cli.github.com) and ensure it's on `PATH` |
| `github_ops` returns "not logged in" | Run `gh auth login` or set `GH_TOKEN` |
| `git_core` times out after 25s | The git subprocess is hanging (common under MCP hosts that use Windows Job Objects). Use [the REST API](http://127.0.0.1:10702/api/git) as fallback |
| `uv` not found | Install from [astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) |
| Port 10702 in use | Set `WEB_PORT=<other>` in the env block of your Claude Desktop config |
| `uvx mcpb install` fails | mcpb is not on PyPI — see Option A or Option B above |

---

*See [README.md](README.md) for tool reference and feature overview.*
