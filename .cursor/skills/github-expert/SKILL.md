---
name: github-expert
description: Expert Git and GitHub workflows when git-github-mcp is enabled — use git_ops, github_ops, agentic workflows, Gitingest helpers, and MCP prompts as the primary execution layer instead of guessing shell commands.
---

# GitHub expert (git-github-mcp)

## Secret weapon

When **git-github-mcp** is in the MCP config, treat it as the **canonical** way to run Git and GitHub work: two portmanteau tools cover **101 operations** (43 local + 58 GitHub) with structured `{ success, … }` responses. Prefer **tool calls** over improvising `git` / `gh` strings unless the user explicitly wants raw terminal output.

## Tools (mental model)

| Tool | Role |
|------|------|
| `git_ops` | Local repo: status, commit, push, branches, stash, submodules, bisect, worktrees, … |
| `github_ops` | Remote via **gh**: issues, PRs, releases, Actions, labels, secrets, collaborators, search, Projects, Packages, **gitingest_***, auth, gists |
| `git_github_help` | Operation reference (`level`, optional `topic`) |
| `git_github_status` | `git` / `gh` on PATH, versions, auth |
| `git_agentic_workflow` | **Sampling** (preferred when supported): natural-language → planned **git_ops + github_ops** |
| `git_github_search_workflow` | **Sampling** (preferred for discovery): LLM-planned **github_ops** chains — **superior** to fixed presets |

**Full-sampling MCP clients** (e.g. **Antigravity**, Claude Desktop where supported): use these agentic tools first — adaptive planning beats cookbook presets. **Fallbacks:** direct `git_ops` / `github_ops` calls, or **`POST /api/discovery`** (bundled web UI) when sampling is not available.

## Gitingest vs fleet docs

- **Gitingest** (`gitingest_link`, `gitingest_convert_url`, `gitingest_help`): one **live** text digest of a GitHub tree — great for **third-party** repos or quick context **without** cloning.
- **`llms.txt` + `llms-full.txt`**: **required**, **committed** pair for **your** MCP repos (curated index + corpus). Gitingest does **not** replace them; see mcp-central-docs `integrations/llms-txt-manifest.md` § Gitingest.

## Prompts (compose with user content)

Use MCP **prompts** for prose templates: `git_commit_message`, `git_release_notes`, `git_pr_description`, `git_review_diff`, `github_issue_template`, `github_debug_workflow`, `git_github_explain_concept`. Fill in diffs/logs; combine with tool results for grounded answers.

## Resources

- `git://skills/concepts` — topic index (includes `gitingest`, `agentic-workflows`).
- `git://skills/{topic}` — short lecture notes for tutoring.

## Anti-patterns

- Don’t duplicate `gh` search logic in prose when `code_find_repos` / `search_code` exists.
- Don’t use Gitingest as an excuse to skip maintaining **`llms.txt` / `llms-full.txt`** on repos you ship.
