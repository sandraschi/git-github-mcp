# Onboarding — git-github-mcp

First-timer setup: get `gh` authenticated so the server (and your AI agent)
can actually reach GitHub. Takes about 5 minutes. No money, no credit card —
a free GitHub account is enough for everything here.

## 1. Install the CLIs

```powershell
winget install Git.Git --accept-source-agreements --accept-package-agreements
winget install GitHub.cli --accept-source-agreements --accept-package-agreements
# Close and reopen PowerShell so PATH updates apply
```

macOS: `brew install git gh`. The server auto-discovers `gh.exe` in
`Program Files`, Scoop shims, Winget and `WindowsApps` — no PATH surgery needed.

## 2. Authenticate with GitHub

```powershell
gh auth login
```

Choose **GitHub.com → HTTPS → Yes (browser flow)** and complete the
one-time code in your browser. Verify:

```powershell
gh auth status
```

You should see `Logged in to github.com`. The server's `git_github_status`
tool reports the same state to your agent (`gh.auth: ok`).

## 3. PAT alternative (headless boxes)

If browser login is impossible, create a classic token at
`github.com → Settings → Developer settings → Personal access tokens`
(scopes: `repo`, `read:org`, `workflow`) and expose it as `GH_TOKEN`
in the MCP server `env` block (see [CONFIGURATION.md](CONFIGURATION.md)).
`gh auth login --with-token` works too. Prefer OAuth login — tokens in
config files are a leak waiting to happen.

## 4. What you get after this

- `github_ops` (repos, issues, PRs, releases, workflows, stars, search) works.
- The webapp `/ci`, `/stars`, `/breakfast` pages light up with live data.
- The agentic workflows (`git_agentic_workflow`, `git_github_search_workflow`)
  need a **sampling-capable client** (Claude Desktop, Antigravity). No
  server-side API keys: the client model does the planning, the server
  executes. The web `/chat` page optionally uses a local Ollama model
  (`OLLAMA_MODEL`, default `gemma3:12b`) — cloud keys are never required.

## 5. Sanity check

In Claude Desktop: *"What is the git status of my current repo?"* → a
structured `git_core` response. On the webapp: green `GIT: OK / GH: OK`
badges in the hero. If either fails, see
[TROUBLESHOOTING.md](TROUBLESHOOTING.md).
