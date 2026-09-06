# Tool Reference

12 MCP tools (portmanteau pattern: one tool, `operation` enum). All return
`{success, …}` — on failure check `error`, `recovery_options`,
`suggested_fixes`. Interactive explorer: webapp `/tools` page.
`git_github_help(level, topic)` answers this at runtime too.

## `git_core` — everyday git (11 ops)

`init, clone, add, commit, push, pull, fetch, status, log, diff, show`.
Key params: `repo_path`, `message`, `files`, `all_files`, `amend`,
`remote`, `branch`, `force`, `set_upstream`, `repo_url`, `target_dir`,
`depth` (shallow clones), `max_count`, `commit`/`commit2`, `oneline`.

```python
git_core(operation="status", repo_path="D:/Dev/repos/foo")
git_core(operation="clone", repo_url="https://github.com/o/r", depth=1)
```

## `git_branch` — branches, stash, tags (14 ops)

`branch_list/create/switch/delete/rename/merge`, `rebase`,
`stash/stash_pop/stash_list/stash_drop`, `tag_list/tag_create/tag_delete`.

## `git_admin` — history surgery + subprojects (17 ops)

`remote_list/add/remove`, `reset`, `revert`, `cherry_pick`, `clean`,
`submodule_add/update/sync/status`,
`bisect_start/bad/good/reset`, `worktree_add/list/remove`.

## `git_blame` — line blame (1 op)

`blame` with optional `commit` ref.

## `github_ops` — GitHub via gh CLI (66 ops)

Repos: `repo_list/view/create/fork/clone/delete/rename/archive`,
`show_repo` (card), `user_repos_full`.
Issues/PRs: `issue_list/view/create/close/comment`,
`pr_list/view/create/merge/checkout/close/comment` (+ `comments`,
`updatedAt` for triage).
Releases: `release_list/view/create/update/delete`.
Workflows: `workflow_list/view/runs/run/rerun/cancel/enable/disable`.
Gists, labels, secrets (`secrets_list/set/delete`), collaborators,
projects, packages.
Stars: `stars_summary`, `stars_per_repo`, `stars_history` (bucket
trajectory — needs `gh auth`, uses `star+json` accept header).
Search: `search_repos`, `search_repos_topic`, `search_repos_by_topic`,
`search_issues`, `search_code` (+ `pretty`, `code_find_repos`).
Gitingest: `gitingest_link/convert_url/help`.
`auth_status` (+ gh login/logout guidance).

```python
github_ops(operation="pr_list", owner="o", repo="r", state="open", limit=50)
github_ops(operation="search_code", query="webServer", extension="ts")
```

## `fleet_morning_digest` — daily maintainer scan

Open PRs/issues per repo, stale flags, notifications since last run.
`deliver="file,aiwatcher"` (also `robofang`); state in
`%LOCALAPPDATA%/git-github-mcp`. CLI: `uv run python
scripts/run_morning_digest.py --deliver file,aiwatcher`.

## `fleet_ops` — fleet toolkit (15 ops + suite)

`registry_load`, `port_audit`, `docs_gate`, `quarantine_report`,
`ci_pulse`, `dependabot_digest`, `mention_inbox`, `ack_drafts`,
`local_dirty`, `release_drift`, `grade_snapshot`, `gitingest_bundle`,
`runner_status`, `weekly_retro`, `council_payload`, `full_suite`.

## `git_github_status` / `show_status_card` / `git_github_help`

`git_github_status(level)` — git/gh versions + auth state.
`show_status_card()` — same as a rich in-chat Prefab card (`app=True`).
`git_github_help(level, topic)` — contextual help.

## Agentic workflows (sampling — need a capable client)

`git_agentic_workflow(task, repo_path, owner, repo)` and
`git_github_search_workflow(task, owner, repo, limit)` plan with the
client model via `ctx.sample()`, then execute tool steps. Without
sampling they return a clean error — call the base tools directly.

## Resources & prompts

Resources: `git://repo/*`, `github://owner/repo/*`, `git://skills/*`.
Prompts: `git_commit_message`, `git_release_notes`, `git_pr_description`,
`git_review_diff`, `github_issue_template`, `github_debug_workflow`,
`git_github_explain_concept`. REST equivalents under `/api/*` (see
[ARCHITECTURE.md](ARCHITECTURE.md)).
