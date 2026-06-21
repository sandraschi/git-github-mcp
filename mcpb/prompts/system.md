# git-github-mcp — Core Capabilities

## Overview

git-github-mcp is a FastMCP 3.4.2+ server that provides comprehensive Git and GitHub operations through a set of portmanteau tools. It bridges local Git repositories with the GitHub API via the gh CLI, enabling LLM agents to perform version control operations, repository management, issue tracking, and fleet-wide maintainer tasks from a single MCP interface.

## Architecture

The server runs a dual-transport architecture: STDIO for Claude Desktop integration, and an optional HTTP bridge on port 10702 for web dashboard access and REST API fallback. Both transports share the same tool registry, enabling seamless switching between modes.

### Transport Layer
- STDIO mode: Default for Claude Desktop, Cursor, and other MCP clients. Uses JSON-RPC over stdin/stdout with no network overhead.
- HTTP mode: FastMCP streamable HTTP at /mcp on port 10702, with FastAPI REST bridge at /api/*, /health, /api/capabilities, /api/logs, and static file serving for the React webapp.

### Tool Architecture
The server exposes 7 portmanteau tools plus 2 standalone tools, covering approximately 120 distinct operations across Git and GitHub domains. Portmanteau tools use a string `operation` discriminator to select the specific action, reducing tool count while maintaining full functionality.

## Tool Reference

### git_core (11 operations)
Core Git workflow operations: init, clone, add, commit, push, pull, fetch, status, log, diff, show. These handle the day-to-day version control tasks for any local Git repository. All operations include async timeout handling (180s for network ops, 25s for local ops) and structured error responses with recovery suggestions.

Key parameters include: repo_path (target directory), message (for commits), files (for add), all_files (stage everything), amend (amend last commit), remote (remote name), branch (target branch), force (force-with-lease push), set_upstream (track remote), repo_url (for clone), target_dir (clone destination), initial_branch (init branch name), depth (shallow clone depth), max_count (log limit), oneline (compact log), commit/commit2 (diff range), file_path (blame target).

### git_branch (14 operations)
Branch lifecycle management: branch_list, branch_create, branch_switch, branch_delete, branch_rename, branch_merge, rebase, stash, stash_pop, stash_list, stash_drop, tag_list, tag_create, tag_delete. Supports daily branching workflows with force-delete for unmerged branches.

| Operation | Required | Description |
|-----------|----------|-------------|
| branch_list | — | List all branches with verbose info |
| branch_create | branch | Create and switch to new branch |
| branch_switch | branch | Switch to existing branch |
| branch_delete | branch | Delete branch (-d or -D with force) |
| branch_rename | branch, source_branch | Rename branch |
| branch_merge | source_branch | Merge source into current |
| rebase | source_branch | Rebase onto source |

### git_admin (16 operations)
Administrative Git operations: remote_list, remote_add, remote_remove, reset, revert, cherry_pick, clean, submodule_add, submodule_update, submodule_sync, submodule_status, bisect_start, bisect_bad, bisect_good, bisect_reset, worktree_add, worktree_list, worktree_remove. Handles advanced repo maintenance.

| Operation | Required | Description |
|-----------|----------|-------------|
| reset | — | Reset HEAD (soft/mixed/hard) |
| revert | commit | Revert a commit |
| cherry_pick | commit | Cherry-pick a commit |
| clean | — | Remove untracked files |
| bisect_start | — | Start bisect session |
| worktree_add | worktree_path | Add linked worktree |

### git_blame (1 operation)
Annotate file lines with commit information: author, timestamp, and summary for each line. Uses git blame --line-porcelain output for structured parsing.

### github_ops (58 operations)
Comprehensive GitHub operations via the gh CLI. Covers repos (list/view/create/fork/clone/delete/rename/archive), issues (list/view/create/close/comment), pull requests (list/view/create/merge/checkout/close/comment), releases (list/view/create/delete/update), Actions workflows (list/run/runs/cancel/disable/enable), labels (list/create/delete), secrets (list/set/delete), collaborators (add/remove), search (repos/issues/code/topic), Projects (list/view/create/delete/edit), Packages (list/view/delete), Gitingest helpers, auth_status, and gist_list.

All operations use the gh CLI with non-interactive mode (GH_PROMPT_DISABLED=1, GIT_TERMINAL_PROMPT=0) to prevent hangs in automated execution.

### git_agentic_workflow (sampling)
Multi-step autonomous Git+GitHub workflow using MCP sampling. The host LLM receives a natural language task and generates a JSON plan with ordered tool calls. The server executes each step and returns structured results with success tracking. Falls back gracefully when sampling is unavailable.

### git_github_search_workflow (sampling)
GitHub discovery and search workflow using MCP sampling. Optimized for research tasks like finding repos by topic, scanning for code patterns, and assembling repo intelligence. Supports limit control and owner/repo scoping.

### fleet_morning_digest
Breakfast runner that scans registered fleet repos for open PRs, stale threads, and new notifications. Configurable via fleet_repos parameter, FLEET_REPOS_FILE env, or config/fleet-repos.txt. Supports delivery to file, aiwatcher, or robofang bridge.

### fleet_ops (16 operations)
Full fleet maintainer toolkit: registry_load, port_audit, docs_gate, quarantine_report, ci_pulse, dependabot_digest, mention_inbox, ack_drafts, local_dirty, release_drift, grade_snapshot, gitingest_bundle, runner_status, weekly_retro, council_payload, full_suite.

## Resources

The server exposes several MCP resources for live introspection:
- git://repo/status — current repo status
- git://repo/log — recent commit log
- git://{repo_path}/status — status for a specific path
- git://{repo_path}/log — log for a specific path
- github://{owner}/{repo}/issues — open issues
- github://{owner}/{repo}/prs — open PRs
- git://skills/concepts — concept index
- git://skills/{topic} — focused cheat-sheet for a topic

## Prompts

Seven built-in MCP prompts for common Git/GitHub workflows:
- git_commit_message — conventional commit from staged diff
- git_release_notes — release notes from commit log
- git_pr_description — PR description from branch/commits
- git_review_diff — code review from diff
- github_issue_template — issue body from template type
- github_debug_workflow — debug failing Actions workflow
- git_github_explain_concept — teach Git/GitHub concepts

All prompts follow the SOTA docstring pattern with typed Annotated parameters and structured return documentation.

## Security Model

Commands are executed as list-based subprocesses (no shell=True) to prevent shell injection. The gh CLI is run with no-prompt env vars to prevent interactive credential dialogs. Git operations use CREATE_NO_WINDOW on Windows to avoid console flash. Hardcoded git binary path bypasses cmd.exe wrappers that can deadlock in consoleless processes.

## Dual-Transport Configuration

The server supports three transport modes configured via MCP_TRANSPORT env or CLI flags:
- stdio (default): JSON-RPC over stdin/stdout for Claude Desktop
- http: FastMCP streamable HTTP protocol
- sse: Legacy Server-Sent Events (deprecated, use http)

## Environment Variables

Core configuration:
- MCP_TRANSPORT: Transport mode (stdio|http|sse)
- MCP_HOST: Bind address for HTTP (default 127.0.0.1)
- MCP_PORT: HTTP port (default 10702)
- MCP_PATH: HTTP endpoint path (default /mcp)
- WEB_PORT: Web bridge port (default 10702)
- WEB_HOST: Web bridge host (default 127.0.0.1)

Fleet configuration:
- GIT_GITHUB_FLEET_OWNER: Default fleet owner (default sandraschi)
- GIT_GITHUB_FLEET_REPOS_FILE: Path to fleet repos file
- GIT_GITHUB_DIGEST_DELIVER: Comma-separated delivery targets
- GIT_GITHUB_STALE_DAYS: Days before PR is stale (default 7)
- GIT_GITHUB_MCP_LOG_MAX_ENTRIES: Ring buffer size (default 2000)

## Error Handling

All tools return structured dicts with success boolean, operation name, and either result data or error diagnostics. Error responses include recovery_options (actionable steps) and suggested_fixes (tool calls to recover). Timeout handling wraps Git subprocesses with operation-aware timeouts (180s network, 25s local). Async operations run in thread pools or asyncio subprocess exec to prevent event loop blocking.
