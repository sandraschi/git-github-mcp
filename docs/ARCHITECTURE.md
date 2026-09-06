# Architecture

## Transports

One server, three ways in (see `src/git_github_mcp/transport.py`):

| Mode | How | Serves |
|------|-----|--------|
| `stdio` (default) | `uv run git-github-mcp` / `--stdio` | MCP for Claude Desktop. With `GIT_GITHUB_WEB=1`, the FastAPI bridge also starts on `WEB_PORT` in a daemon thread |
| `http` | `--http --port 10713` (or `MCP_TRANSPORT=http`) | MCP over streamable HTTP at `/mcp` **only** — no `/health`, no REST |
| `sse` | `--sse` | Deprecated, use `http` |

The full REST + web UI bridge is `web_app`
(`uv run uvicorn git_github_mcp.server:web_app --host 127.0.0.1 --port 10713`),
which is also what `fleet-start` launches and what Playwright e2e asserts.

## Ports

Backend `10713` · Vite frontend `10714` (dev proxies `/api` → `:10713`;
`preview` serves the `dist/` build on the same port). Registered in
mcp-central-docs `WEBAPP_PORTS.md`. `start.ps1` clears the port before
binding; a stale `git-github-mcp.exe` produces a warning, not a crash loop.

## Request flow

```
Claude Desktop (stdio) ─┐
                        ├─▶ FastMCP tools ─▶ git.exe / gh.exe subprocesses
Vite :10714 ─▶ FastAPI :10713 (REST /api/*) ─┘        (shell=False, DEVNULL stdin,
                                                       no-prompt env, oily timeouts:
                                                       25 s local / 180 s network)
```

- Every tool returns `{success, …}` with `recovery_options` / suggested
  fixes (`src/git_github_mcp/utils/response.py`).
- `web_app` lifespan reuses the MCP HTTP app lifespan; `GET /health`,
  `/api/status`, `/api/tools`, `/api/git`, `/api/github`,
  `/api/morning-digest`, `/api/fleet-ops`, `/api/fleet-suite*`,
  `/api/discovery`, `/api/apps*`, `/api/chat`, `/api/skills*`,
  `/api/llm/discover`, `/api/v1/*`. When `web/dist/` is built it is
  mounted statically at `/`.
- Agentic tools (`git_agentic_workflow`, `git_github_search_workflow`) plan
  via `ctx.sample()` (client model) then execute `git_core`/`github_ops`
  steps — no server-side LLM keys.
- Fleet suite (`fleet_ops`, `fleet_morning_digest`) reads the registry /
  `config/fleet-repos.txt`, persists state under `%LOCALAPPDATA%`,
  delivers to file / aiwatcher / robofang.

## Layout

`src/git_github_mcp/` — `server.py` (tools + REST + lifespan),
`transport.py` (CLI/env), `tools/` (git + github implementations),
`services/` (fleet, digest, discovery), `utils/` (gh runner, responses,
formatting), `web.py`, `logs_api.py`, `auth.py`, `activity_log.py`.
`web/` — Vite + React + Tailwind + Zustand frontend (`src/pages/`,
`e2e/smoke.spec.ts`). `native/` — Tauri shell. `mcpb/` — Claude Desktop
bundle staging (regenerated on pack, do not hand-edit).
