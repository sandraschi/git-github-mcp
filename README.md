# Git & GitHub CLI MCP Server (v0.4.1)

[![FastMCP Version](https://img.shields.io/badge/FastMCP-3.2.0-blue?style=flat-square&logo=python&logoColor=white)](https://github.com/sandraschi/fastmcp) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Linted with Biome](https://img.shields.io/badge/Linted_with-Biome-60a5fa?style=flat-square&logo=biome&logoColor=white)](https://biomejs.dev/) [![Built with Just](https://img.shields.io/badge/Built_with-Just-000000?style=flat-square&logo=gnu-bash&logoColor=white)](https://github.com/casey/just)

**Industrial-grade Git and GitHub orchestration** for the Agentic Revolution. Built for developers who need their AI implementation engines to interact with repositories without environment friction.

**Stack:** v0.4.1  FastMCP 3.2.0+  Python 3.12+  Windows 10/11  GitHub CLI (gh)  

**Industrial Disclosure:** This server is part of the **[Agentic Revolution Manifesto](https://github.com/sandraschi/mcp-central-docs/blob/master/manifesto/AGENTIC_REVOLUTION.md)**. All tools are designed for machine-native consumption, providing high-fidelity telemetry and crash-resistant automation for the 135+ repository Alsergrund fleet.

---

### 🚀 Zero-Friction Orchestration
If your AI agent fails to perform Git or GitHub actions because of `gh` CLI path issues or authentication gaps, this server solves that. 

- **Automatic Discovery**: It finds your `gh.exe` installation in standard Windows locations (Program Files, Scoop, Winget) without requiring a system `PATH` entry.
- **100+ Tools**: Complete coverage for Git (local) and GitHub (remote) workflows.
- **Industrial Strength**: Zero "fluff"—just direct, actionable results for commits, PRs, issues, and repository management.
- **SOTA v14.x Automated Startup**: Root-level `start.ps1` and `start.bat` for one-click deployment of the full FastAPI + Vite stack.


---

## Capabilities

### Git Operations (43 actions)

| Group | Operations |
|-------|-----------|
| CORE | init, clone, add, commit, push, pull, fetch, status |
| INSPECT | log, diff, show, blame |
| BRANCH | create, switch, delete, merge, rebase, list |
| REMOTE | list, add, remove |
| STASH | stash, pop, list, drop |
| TAG | list, create, delete |
| UNDO | reset, revert, cherry_pick |
| CLEANUP | clean |
| SUBMODULE | add, update, sync, status |
| BISECT | start, bad, good, reset |
| WORKTREE | add, list, remove |

### GitHub Operations (58 actions)

| Group | Operations |
|-------|-----------|
| REPOS | list, view, create, fork, clone, delete, rename, archive |
| ISSUES | list, view, create, close, comment |
| PRs | list, view, create, merge, checkout, close, comment |
| RELEASES | list, view, create, upload, delete |
| GISTS | list, view, create, edit, delete |
| WORKFLOWS | list, view, run, enable, disable |
| LABELS | list, create, edit, delete |
| SECRETS | list, set, delete |
| ORGS | list, view |
| USERS | user_view |
| SEARCH | repos, issues, prs, code, users |
| AUTH | status, login, logout |

---

## Design Principles

- **Integrated Tooling**: Consolidates multiple CLI utilities into a single, reliable server interface.
- **Structured Feedback**: Every tool returns a consistent `result` object for easy agent parsing.
- **Low Friction**: Minimal configuration required. If `gh` is installed, it works.

## Maintainer: PR triage (small repos)

Silence reads as indifference. You do not need a bot on day one: use **`github_ops`** to list open PRs and post a short first reply.

1. **List open PRs** (includes **`comments`** and **`updatedAt`** so you can spot threads that sat cold):

   `github_ops(operation="pr_list", owner="YOUR_USER", repo="YOUR_REPO", state="open", limit=50)`

2. **Acknowledge** so the author knows it was seen — **`github_ops(operation="pr_comment", owner=..., repo=..., pr_number=..., body="...")`**. Example tone (edit to your voice):

   > Thanks for the PR — I maintain this in spare time and do not always see notifications quickly. I have read it and will review properly within the next few days; I will comment here if I need changes.

3. **GitHub.com:** for repos you care about, set **Watch** to **All activity** (or at least **Participating**) so PRs are not only visible when you open the site.

4. Optional: add a **PR template** or **CONTRIBUTING.md** line setting expectations (e.g. “I try to acknowledge within 48h; deep review may take longer”).

5. **Web inbox:** with the FastAPI + Vite app running, open **`/inbox`** — **Pull requests & Issues** with optional **fleet** mode (many `owner/repo` lines), stale highlights, and the same data as `github_ops`. A **supervisor** stack (OpenClaw, OpenManus, RoboFang, OpenClaude, etc.) can run a **daily heartbeat** that calls `pr_list` / `issue_list` across your repo list; this page is the human-facing mirror.

6. **Fleet doc (mcp-central-docs):** **[GITHUB_MAINTAINER_HEARTBEAT.md](https://github.com/sandraschi/mcp-central-docs/blob/master/patterns/GITHUB_MAINTAINER_HEARTBEAT.md)** — where the schedule lives, robofang council hook, prompt sketch.

This does not replace a fair review — it reduces “I wasted hours in the void” as the default story.


## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
- **Security**: Automated audits via `bandit` and `safety`.

## License

MIT
