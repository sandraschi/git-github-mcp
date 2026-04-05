# git-github-mcp

FastMCP 3.1.1+ hardened substrate for Git and GitHub operations. v1.20 non-interactive safety enforced for reliable AI orchestration.

## Tools

| Tool | Actions | Description |
|------|---------|-------------|
| `git_ops` | 43 | Local Git operations; **v1.20 High-Fidelity Status** parsing |
| `github_ops` | 58 | GitHub operations via `gh` CLI (+ Gitingest URL helpers, no `gh`) |
| `git_agentic_workflow` | agentic | Sampling: natural-language Git **+** GitHub multi-step plans |
| `git_github_search_workflow` | agentic | Sampling: discovery / search chains on GitHub data only |
| `git_github_help` |  | Contextual help (level: basic/intermediate/advanced) |
| `git_github_status` |  | Git and gh CLI availability, versions, auth state |

### MCP prompts

| Prompt | Use |
|--------|-----|
| `git_commit_message` | Conventional commit from staged diff |
| `git_release_notes` | Release notes from `git log` range |
| `git_pr_description` | PR body from branch + commits |
| `git_review_diff` | Structured code review |
| `github_issue_template` | Issue body (bug / feature / docs / question) |
| `github_debug_workflow` | Actions failure triage (pair with `workflow_runs` when possible) |
| `git_github_explain_concept` | Tutor mode (e.g. rebase, **gitingest**, **agentic-workflows**) |

### git_ops  43 actions

| Group | Operations |
|-------|-----------|
| CORE | init, clone, add, commit, push, pull, fetch, **status (porcelain-v1)** |
| INSPECT | log, diff, show, blame |
| BRANCH | branch_list, branch_create, branch_switch, branch_delete, branch_merge, rebase |
| REMOTE | remote_list, remote_add, remote_remove |
| STASH | stash, stash_pop, stash_list, stash_drop |
| TAG | tag_list, tag_create, tag_delete |
| UNDO | reset, revert, cherry_pick |
| CLEANUP | clean |
| SUBMODULE | submodule_add, submodule_update, submodule_sync, submodule_status |
| BISECT | bisect_start, bisect_bad, bisect_good, bisect_reset |
| WORKTREE | worktree_add, worktree_list, worktree_remove |

### github_ops  58 actions

| Group | Operations |
|-------|-----------|
| REPOS | repo_list, repo_view, **show_repo**, repo_create, repo_fork, repo_clone, repo_delete, repo_rename, repo_archive |
| ISSUES | issue_list, issue_view, issue_create, issue_close, issue_comment |
| PRs | pr_list, pr_view, pr_create, pr_merge, pr_checkout, pr_close, pr_comment |
| RELEASES | release_list, release_view, release_create, release_delete, release_update |
| ACTIONS | workflow_list, workflow_run, workflow_runs, workflow_cancel, workflow_disable, workflow_enable |
| LABELS | label_list, label_create, label_delete |
| SECRETS | secrets_list, secrets_set, secrets_delete |
| COLLABORATORS | collaborator_add, collaborator_remove |
| SEARCH | search_repos, **search_repos_topic**, search_issues, search_code (**pretty**), **code_find_repos** |
| PROJECTS | project_list, project_view, project_create, project_delete, project_edit |
| PACKAGES | package_list, package_view, package_delete |
| **GITINGEST** | **gitingest_link**, **gitingest_convert_url**, **gitingest_help** |
| MISC | auth_status, gist_list |

**Discovery:** `code_find_repos` builds GitHub code-search queries (e.g. `extension:bak` + `user:YOU`) and returns a **markdown** table plus **unique_repositories**. `show_repo` returns **content** as Markdown, HTML, or JSON for quick preview.

### Gitingest ([gitingest.com](https://gitingest.com))

Turn a **public GitHub repo** (or a **branch subpath**) into one **LLM-friendly digest** (file tree + concatenated sources + token stats). Upstream rule: replace **`hub`** with **`ingest`** in **`github.com`**  **`gitingest.com`**.

| Operation | Purpose |
|-----------|---------|
| `gitingest_help` | Markdown explainer: what Gitingest is for, vs **`llms.txt` / `llms-full.txt`**, links |
| `gitingest_link` | Build `gitingest_url` from `owner`, `repo`, optional `ref`, optional `subpath` |
| `gitingest_convert_url` | Paste a `https://github.com/...` URL  `gitingest_url` |

**Relation to `llms.txt`:** Gitingest is **live** and **raw**; fleet **`llms.txt` + `llms-full.txt`** are **curated, versioned** entry points. Use both  see [mcp-central-docs `integrations/llms-txt-manifest.md`](https://github.com/sandraschi/mcp-central-docs/blob/master/integrations/llms-txt-manifest.md) (Gitingest section).

### Agentic search workflow

Use `git_github_search_workflow` when you want the model to plan and run multiple search/discovery steps.

Examples:

- `task="find repos with bak file dross for my account"`
- `task="list stale GitHub projects and summarize likely cleanup candidates"`
- `task="find repos tagged mcp with low activity and open issues"`

## Requirements

- Python 3.12+
- Git
- [GitHub CLI (`gh`)](https://cli.github.com/)  see [GitHub CLI authentication](#github-cli-authentication-gh) below

## GitHub CLI authentication (`gh`)

### When it is required

| Area | Needs `gh` + login? |
|------|---------------------|
| **`git_ops`** (local Git only) | No |
| **`github_ops`** (issues, PRs, `gh api`, etc.) | **Yes**  every call shells out to `gh`; without auth you get errors from the CLI |
| **Gitingest helpers** (`gitingest_link`, `gitingest_convert_url`, `gitingest_help`) | **No**  URL building only (reading public repos in a browser is separate) |
| **`git_agentic_workflow` / `git_github_search_workflow`** | **Yes**, whenever the plan touches GitHub (not for pure `git_ops` plans) |
| **Web dashboard** (repos, issues, PRs, discovery calling GitHub) | **Yes**  same backend as `github_ops` |

### How and where you authenticate

1. Install `gh` and ensure it is on `PATH` (same environment you use to run the MCP server or `uv run git-github-mcp`).
2. In a **normal terminal** (PowerShell or cmd), run:
   ```powershell
   gh auth login
   ```
   Choose **GitHub.com**, **HTTPS**, then **Login with a web browser** or paste a **personal access token** when prompted.
3. **Verify** in that terminal:
   ```powershell
   gh auth status
   ```
   Or from an MCP client, call tool **`git_github_status`** and inspect `result.gh.auth` (`ok` vs `not logged in`).

**Where credentials live:** `gh` stores the token in the OS-backed store and config under your user profile (on Windows, typically under `%LOCALAPPDATA%\GitHub CLI\`). The MCP process uses **your** `gh` when it is started as you (Cursor terminal, `uv run`, etc.).

**Extra scopes:** Some `github_ops` actions (e.g. Projects) may require `gh auth refresh -s project` after login.

## Install

```powershell
git clone https://github.com/sandraschi/git-github-mcp.git
cd git-github-mcp
pip install -e ".[dev]"
```

Or via uv:

```powershell
uvx git-github-mcp
```

## Claude Desktop Config

```json
{
  "mcpServers": {
    "git-github-mcp": {
      "command": "uv",
      "args": ["--directory", "D:/Dev/repos/git-github-mcp", "run", "git-github-mcp"]
    }
  }
}
```

## Run standalone

```powershell
python -m git_github_mcp
```

## Webapp

**Fleet v1.20 Standard:** Premium React/Tailwind UI with glassmorphism, HSL theme tokens, and real-time health indicators. The **Dashboard** aggregates local Git status (staged/unstaged) and GitHub fleet telemetry.

**Ports (fleet):** backend **10702**, Vite frontend **10703** (see `mcp-central-docs/operations/WEBAPP_PORTS.md`). The web UI talks to the API via `VITE_API_URL` (defaults to `http://localhost:10702`).

**GitHub:** Complete [`gh auth login`](#github-cli-authentication-gh) before expecting repos/PRs/issues to load.

```powershell
cd web
npm install
.\start.ps1
```

`web/start.ps1` clears both ports, starts the FastAPI backend and Vite, then **opens the default browser** to `http://localhost:10703` as the last step.

## MCPB Package

```powershell
.\mcpb\pack.ps1
```

Output: `dist/git-github-mcp.mcpb`

## Design

- Portmanteau pattern: all local git work in one tool, all GitHub work in another
- Dialogic responses: every call returns `success`, `result`, `recommendations`, `next_steps`
- Literal enums for operation discoverability
- FastMCP 3.1+ server lifespan and transport

## License

MIT
