# Troubleshooting

Problem → Cause → Fix, flat list. For setup issues also see
[ONBOARDING.md](ONBOARDING.md); for install paths see `INSTALL.md`.

## `github_ops` — "gh CLI not found"
**Cause**: `gh` not installed or not discoverable.
**Fix**: `winget install GitHub.cli`, reopen PowerShell, `gh auth login`.
The server probes `Program Files`, Scoop, Winget and `WindowsApps` itself.

## `github_ops` — "not logged in"
**Cause**: No `gh` auth session.
**Fix**: `gh auth login` (browser flow) or set `GH_TOKEN` in the server
`env` block. Check with `gh auth status` and the `git_github_status` tool.

## `git_core` times out after 25 s (clone/push/pull/fetch)
**Cause**: blanket MCP wrapper timeout; Electron/Windows Job Object stalls.
**Fix**: network ops get 180 s server-side — retry once. For huge repos,
shallow-clone first: `git_core(operation="clone", repo_url="…", depth=1)`.
REST fallback: `POST /api/git`.

## Port 10713 (or 10714) already in use
**Cause**: orphan backend from a killed session (WinError 10048).
**Fix**: `start.ps1` clears the port before binding — prefer it. Manual:
`Get-NetTCPConnection -LocalPort 10713 | Select-Object OwningProcess`,
then stop the owner. A stale `git-github-mcp.exe` holding the port makes
`start.ps1` warn instead of crash-looping.

## Server not in Claude Desktop
**Cause**: bad config JSON or failed startup.
**Fix**: run `uv run git-github-mcp --stdio` in a terminal and read the
error; validate the JSON (no trailing commas); confirm the config path
(`%APPDATA%\Claude\claude_desktop_config.json`); restart Claude Desktop.

## `uvx mcpb` fails
**Cause**: mcpb is npm, not PyPI — expected.
**Fix**: use releases drag-and-drop (Option A) or
`npx @anthropic-ai/mcpb install <repo-url>` (Option B).

## Agentic workflow returns "sampling requires an active MCP session"
**Cause**: `git_agentic_workflow` / `git_github_search_workflow` need
`ctx.sample()` — stdio pipes and plain HTTP without a model can't plan.
**Fix**: call from Claude Desktop / Antigravity, or invoke the underlying
`git_core` / `github_ops` operations directly (deterministic, no LLM).

## `webServer` Playwright timeout on :10713
**Cause**: old `playwright.config.ts` ran the server in stdio mode (fixed
in v0.6.4) — or the port is held by an orphan (see above).
**Fix**: pull latest; `reuseExistingServer` is disabled in CI so the run
always spawns a fresh `uvicorn web_app` backend.

## Biome/TS errors after editing `web/`
**Cause**: formatter or types drifted.
**Fix**: `cd web; npm run check; npm run biome:ci` — or `just fix` from root.
The pre-commit hook blocks commits until both pass.

## `npm ci` fails in `web/`
**Cause**: lock file out of sync after a `package.json` edit.
**Fix**: `cd web; npm install` (regenerates the lock), commit both files.

Still stuck? [Open an issue](https://github.com/sandraschi/git-github-mcp/issues)
with the failing tool call, the `success: false` payload, and (for webapp
issues) the page route + browser console output.
