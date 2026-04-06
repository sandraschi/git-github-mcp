# Git & GitHub CLI MCP Server (v0.4.0)

A reliable, integrated toolset for local Git and GitHub CLI orchestration. Built for developers who need their AI agents to interact with repositories without environment configuration overhead.

### 🚀 What is this?
If your AI agent fails to perform Git or GitHub actions because of `gh` CLI path issues or authentication gaps, this server solves that. 

- **Automatic Discovery**: It finds your `gh.exe` installation in standard Windows locations (Program Files, Scoop, Winget) without requiring a system `PATH` entry.
- **100+ Tools**: Complete coverage for Git (local) and GitHub (remote) workflows.
- **Industrial Strength**: Zero "fluff"—just direct, actionable results for commits, PRs, issues, and repository management.

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

## License

MIT
