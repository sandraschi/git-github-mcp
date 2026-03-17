# git-github-mcp

FastMCP 3.1+ portmanteau server for Git and GitHub operations. Two tools cover the full workflow — no 40-tool explosion.

## Tools

| Tool | Actions | Description |
|------|---------|-------------|
| `git_ops` | 43 | Local Git operations via subprocess |
| `github_ops` | 43 | GitHub operations via `gh` CLI |
| `git_github_help` | — | Contextual help (level: basic/intermediate/advanced) |
| `git_github_status` | — | Git and gh CLI availability, versions, auth state |

### git_ops — 43 actions

| Group | Operations |
|-------|-----------|
| CORE | init, clone, add, commit, push, pull, fetch, status |
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

### github_ops — 43 actions

| Group | Operations |
|-------|-----------|
| REPOS | repo_list, repo_view, repo_create, repo_fork, repo_clone, repo_delete, repo_rename, repo_archive |
| ISSUES | issue_list, issue_view, issue_create, issue_close, issue_comment |
| PRs | pr_list, pr_view, pr_create, pr_merge, pr_checkout, pr_close, pr_comment |
| RELEASES | release_list, release_view, release_create, release_delete, release_update |
| ACTIONS | workflow_list, workflow_run, workflow_runs, workflow_cancel, workflow_disable, workflow_enable |
| LABELS | label_list, label_create, label_delete |
| SECRETS | secrets_list, secrets_set, secrets_delete |
| COLLABORATORS | collaborator_add, collaborator_remove |
| SEARCH | search_repos, search_issues, search_code |
| MISC | auth_status, gist_list |

## Requirements

- Python 3.12+
- Git
- [gh CLI](https://cli.github.com/) — must be authenticated: `gh auth login`

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

Dark React/Tailwind UI for repos, issues, PRs and tool runner.

```powershell
cd web
npm install
.\start.ps1
```

Open http://localhost:11900

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
