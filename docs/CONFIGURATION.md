# Configuration

All settings are environment variables. In Claude Desktop, set them in the
server's `env` block (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "git-github-mcp": {
      "command": "uv",
      "args": ["--directory", "C:\\path\\to\\git-github-mcp", "run", "git-github-mcp"],
      "env": { "PYTHONUNBUFFERED": "1", "GH_TOKEN": "ghp_..." }
    }
  }
}
```

## Transport (MCP)

| Variable | Default | Purpose |
|----------|---------|---------|
| `MCP_TRANSPORT` | `stdio` | `stdio` (Claude Desktop) \| `http` (streamable) \| `sse` (deprecated) |
| `MCP_HOST` | `127.0.0.1` | Bind address for HTTP/SSE |
| `MCP_PORT` | `10713` | MCP HTTP port |
| `MCP_PATH` | `/mcp` | MCP endpoint path |
| `MCP_BRIDGE_URLS` | — | Extra bridge URLs (comma-separated) |

CLI flags (`--http`, `--host`, `--port`, `--path`, `--stdio`) override these.

## Web bridge (FastAPI + Vite)

| Variable | Default | Purpose |
|----------|---------|---------|
| `WEB_PORT` | `10713` | Backend listen port |
| `WEB_HOST` | `127.0.0.1` | Backend bind address (frontend Vite dev runs on `10714`) |
| `GIT_GITHUB_WEB` | `0` | `1` = also serve the HTTP bridge alongside stdio |
| `GIT_GITHUB_WEB_USER` | `sandra` | Basic-auth username for the web bridge |
| `GIT_GITHUB_WEB_PASS` | `vienna2026` | Basic-auth password — **change this** if you expose the port |

## GitHub auth

| Variable | Default | Purpose |
|----------|---------|---------|
| `GH_TOKEN` | — | PAT override (skips `gh auth login`; see [ONBOARDING.md](ONBOARDING.md)) |

## Fleet / maintainer suite

| Variable | Default | Purpose |
|----------|---------|---------|
| `GIT_GITHUB_FLEET_OWNER` | `sandraschi` | Default owner for fleet scans |
| `GIT_GITHUB_FLEET_REPOS_FILE` | — | `owner/repo` list file (else `config/fleet-repos.txt`, else registry) |
| `FLEET_REGISTRY_PATH` | `mcp-central-docs/operations/fleet-registry.json` | Fleet registry location |
| `FLEET_WEBAPP_PORTS_PATH` | `mcp-central-docs/operations/WEBAPP_PORTS.md` | Port registry (collision audits) |
| `FLEET_REPOS_ROOT` | `D:/Dev/repos` | Workspace root for local scans |
| `GIT_GITHUB_MCP_STATE_DIR` | `%LOCALAPPDATA%/git-github-mcp` | State dir override |
| `GIT_GITHUB_MAINTAINER_LOGIN` | — | Your login (maintainer-vs-stranger stale triage) |
| `GIT_GITHUB_STALE_DAYS` | `7` | Stale threshold for PR/issue flags |
| `GIT_GITHUB_DIGEST_DELIVER` | — | Default digest sinks (`file`, `aiwatcher`, `robofang`) |
| `GIT_GITHUB_DIGEST_OUTPUT` | — | Digest file output path |
| `AIWATCHER_HTTP_URL` | `http://127.0.0.1:10946` | aiwatcher ingest endpoint |
| `ROBOFANG_BRIDGE_URL` | `http://127.0.0.1:10871` | robofang bridge pulse endpoint |
| `SCRAPER_MCP_DIR` / `SCRAPER_MCP_URL` | `D:/Dev/repos/scraper-mcp` / `http://127.0.0.1:10989` | Scraper companion for bundles |

## Chat / misc

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_MODEL` | `gemma3:12b` | Local model for web `/chat` (Ollama; no cloud keys needed) |
| `GIT_GITHUB_MCP_LOG_MAX_ENTRIES` | `10000` (clamped 100–50000) | Activity log ring size |
| `PYTHONUNBUFFERED` | — | Set to `1` in Claude Desktop config |
