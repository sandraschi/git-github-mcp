# Changelog

## 0.4.0 (2026-03-20)

### Agentic discovery + skills
- Added `git_github_search_workflow` tool for sampling-driven multi-step discovery/search plans using `github_ops`
- Added resources:
  - `git://skills/concepts` (topic index)
  - `git://skills/{topic}` (focused lecture notes, starting with `rebase`, `merge-vs-rebase`, `cherry-pick`)
- Added prompt `git_github_explain_concept(concept, level)` for tutor-style explanations

### Webapp lectures and lookup
- Added `/lectures` page with searchable Git/GitHub mini-lectures, commands, and pitfalls
- Added sidebar navigation entry for Lectures
- Extended command chat examples with `github find-bak <owner>` and `github show <owner> <repo>`

### Gitingest (LLM digest URLs)
- **github_ops:** `gitingest_link`, `gitingest_convert_url`, `gitingest_help` — [Gitingest](https://gitingest.com) URLs + docs vs `llms.txt` / `llms-full.txt`
- New `utils/gitingest_urls.py`
- Skills: `git://skills/concepts` includes `gitingest`; `git://skills/gitingest` lecture notes

### github_ops: 43 → 58 actions (includes Gitingest trio above)
- **show_repo** — same metadata as `repo_view` plus **`content`** as Markdown, HTML, or JSON (`output_format`)
- **search_repos_topic** — discover repos by GitHub **topic** (repo tag); optional `owner` scopes `user:…`, optional `query` adds search terms
- **code_find_repos** — builds a code-search query from `extension`, `path_pattern`, `search_scope`, `owner` (`user:`), and/or `query`; returns **`markdown`** table + **`unique_repositories`**
- **search_code** — `pretty=True` adds **`markdown`** + **`unique_repositories`**
- **Projects** — `project_list`, `project_view`, `project_create`, `project_delete`, `project_edit` (`gh project`; may need `gh auth refresh -s project`)
- **Packages** — `package_list`, `package_view`, `package_delete` via `gh api` (`read:packages` / `write:packages`)

### Prompts, planner strings, and Cursor skill
- Refreshed MCP **prompt** copy (commit, release notes, PR, review, issue, Actions debug, explain) to reference current tools and grounded workflows
- Updated **sampling planner** prompts for `git_agentic_workflow` and `git_github_search_workflow` (58-action surface, Gitingest, signals)
- Skills: `git://skills/agentic-workflows`; expanded `gitingest` notes
- **`.cursor/skills/github-expert/SKILL.md`** — use git-github-mcp as the default execution layer when enabled
- **`mcpb/manifest.json`**: version 0.4.0, 6 tools, 7 prompts, 8 resources, accurate descriptions

### Other
- New `utils/github_format.py` for repo cards and code-search tables
- Tests: `test_github_format.py`, `test_github_ops.py`

## 0.3.0 (2026-03-17)

### git_ops: 30 → 43 actions
- Added `blame` — annotate file lines with commit/author info
- Added `clean` — remove untracked files (`dry_run`, `include_dirs` flags)
- Added `submodule_add`, `submodule_update`, `submodule_sync`, `submodule_status`
- Added `bisect_start`, `bisect_bad`, `bisect_good`, `bisect_reset`
- Added `worktree_add`, `worktree_list`, `worktree_remove`

### github_ops: 25 → 43 actions
- Added `repo_delete`, `repo_rename` (new_name param), `repo_archive`
- Added `pr_close`, `pr_comment`
- Added `release_delete`, `release_update`
- Added `workflow_cancel` (run_id), `workflow_disable`, `workflow_enable`
- Added `label_list`, `label_create`, `label_delete`
- Added `secrets_list`, `secrets_set`, `secrets_delete`
- Added `collaborator_add` (permission param), `collaborator_remove`
- Fixed `repo_view` — removed invalid `openIssuesCount` gh CLI field

### Other
- Updated `help.py` with full operation tables at all three levels
- Updated README with complete operation tables


## 0.2.0 (2026-03-16)

### git_ops: expanded to 30 actions
- Added: fetch, log, diff, show
- Added: branch_list, branch_create, branch_switch, branch_delete, branch_merge, rebase
- Added: remote_list, remote_add, remote_remove
- Added: stash, stash_pop, stash_list, stash_drop
- Added: tag_list, tag_create, tag_delete
- Added: reset, revert, cherry_pick

### github_ops: expanded to 25 actions
- Added: repo_list, repo_view, repo_create, repo_fork, repo_clone
- Added: issue_list, issue_view, issue_create, issue_close, issue_comment
- Added: pr_list, pr_view, pr_create, pr_merge, pr_checkout
- Added: release_list, release_view, release_create
- Added: workflow_list, workflow_run, workflow_runs
- Added: search_repos, search_issues, search_code
- Added: auth_status, gist_list

### Other
- Migrated to FastMCP 3.0+
- Dialogic response pattern (success/error + recommendations/next_steps)
- Literal enums for operation discoverability


## 0.1.0 (2026-02-08)

- Initial release
- git_ops: clone, status, add, commit, push, pull, branch, tag, stash
- github_ops: create_issue, list_issues, create_pr, list_prs, search (via gh CLI)
- FastMCP 2.14.4+, Literal enums for discoverability, dialogic response patterns
