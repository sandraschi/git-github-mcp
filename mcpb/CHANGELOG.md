
## [Unreleased] — 2026-06-14

### Added
- Tauri native wrapper (native/ directory) with bundle.resources + std::process::Command
- CUA-NSIS: just cua-nsis-test recipe, scripts/cua-smoke.py, scripts/cua-nsis-config.json
- Tauri CORS: tauri://localhost origins for WebView API access
- NSIS installer at dist/ and native/target/release/bundle/nsis/

### Changed
- Frontend API calls use absolute http://127.0.0.1:{port} URLs in production build
- CORS middleware includes allow_origin_regex for tauri.localhost
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **`depth` parameter on `git_core`** — Shallow clone support via `--depth N`. Pass `depth=1`
  for large repos (linux kernel, vscode etc.) to fetch only the current tree, completing in
  seconds rather than timing out.
- **Context-aware clone timeout error** — When clone times out, returns a specific message
  explaining the cause and suggesting `depth=1` with a ready-to-run PowerShell fallback.

### Fixed
- **Clone/push/pull/fetch killed by 25s MCP wrapper** — `server.py` had a blanket
  `asyncio.wait_for(timeout=25)` around all git operations. Network ops now get 180s;
  local ops retain 25s. The inner `_run_git_async` subprocess timeout for clone (120s)
  now actually gets a chance to fire.

### Files Changed
- `src/git_github_mcp/server.py`
- `src/git_github_mcp/tools/git_ops.py`

 `git_ops` (43 ops → 1 huge tool) replaced with 4 focused tools:
  - `git_core` (11 ops): status, log, diff, show, init, clone, add, commit, push, pull, fetch
  - `git_branch` (14 ops): branch lifecycle, merge, rebase, stash, tag
  - `git_admin` (16 ops): remote, reset, revert, cherry-pick, clean, submodule, bisect, worktree
  - `git_blame` (1 op): file blame with optional commit ref
- **Dual transport**: Server runs stdio AND HTTP bridge (port 10702) simultaneously
- **REST API**: `/health`, `/api/git`, `/api/github`, `/api/tools`, `/api/status`
- **Conversational error returns**: All tool handlers use `success_response`/`error_response` with `recovery_options` and `suggested_fixes`
- **MCP HTTP mount**: `mcp.http_app()` mounted at `/mcp` for streamable HTTP clients

### Fixed
- **Git subprocess hang on Windows**: `_run_git` now uses `shell=True` + `cmd.exe` wrapper to bypass potential Windows Job Object limits imposed by Electron/Node.js MCP hosts
- **Server-side timeout**: `_run_git_tool` wraps `asyncio.to_thread` with `asyncio.wait_for(timeout=25)` to catch hangs before the MCP client timeout fires
- **Hardcoded git path**: `_GIT_EXE` hardcoded to `C:\Program Files\Git\bin\git.exe` — avoids PATH resolution issues in MCP child processes
- **Entry point**: `__init__.py` exports `main` from `server.py`; `__main__.py` delegates to `server.main()`

### Changed
- **Environment cleanup**: `_git_env()` stripped `GIT_CONFIG_NOSYSTEM` and hardcoded config paths — uses same `_no_prompt_env()` as `github_ops`
- **`-C` flag**: Git working directory set via `git -C <path>` instead of `subprocess.run(cwd=...)` to avoid `lpCurrentDirectory` issues
- **Removed `CREATE_NO_WINDOW`**: Swapped for `shell=True` in `_run_git` to escape job object constraints
- **Ruff clean**: 0 lint errors across all source files

## [0.4.0] - 2026-04-06

### Added
- **Automatic gh Discovery**: Hardened Windows path discovery for `gh.exe` in `C:\Program Files\GitHub CLI` and `scoop` shims.
- **Environment Resilience**: Server now functions correctly even if the system `PATH` is missing key CLI tools (gh, just, winget).

### Changed
- **FastMCP 3.2.0**: Upgraded core framework to latest SOTA for improved tool registry performance and tool-calling reliability.
- **Dependency Refresh**: Updated project metadata and core dependencies.

## [0.3.0] - 2025-03-19
- Initial FastMCP 3.1 implementation.
- Support for 100+ Git and GitHub operations.
