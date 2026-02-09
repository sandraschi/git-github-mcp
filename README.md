# git-github-mcp

FastMCP 2.14.4 portmanteau server for Git and GitHub operations. Uses `gh` CLI for GitHub; avoids the 40-tool explosion.

## Features

- **git_ops**: clone, status, add, commit, push, pull, branch, tag, stash
- **github_ops**: create_issue, list_issues, create_pr, list_prs, search (via `gh` CLI)
- SOTA: Literal enums for discoverability, dialogic tool returns (success/error + recommendations/next_steps), server lifespan

## Requirements

- Python 3.12+
- Git
- [gh CLI](https://cli.github.com/) (must be authenticated: `gh auth login`)

## Install

```powershell
pip install -e ".[dev]"
```

## Run

```powershell
python -m git_github_mcp
```

Or via MCP config:

```json
{
  "mcpServers": {
    "git-github": {
      "command": "python",
      "args": ["-m", "git_github_mcp"]
    }
  }
}
```

## Tools

| Tool | Operations |
|------|------------|
| git_ops | clone, status, add, commit, push, pull, branch, tag, stash |
| github_ops | create_issue, list_issues, create_pr, list_prs, search |

## Webapp

Dark React Tailwind UI for repos, issues, PRs, and tool runner.

```powershell
cd web
npm install
npm run build
python server.py
```

Open http://localhost:5180. Or dev mode: `npm run dev` (Vite) + `python server.py` (backend on 5180).

## License

MIT
