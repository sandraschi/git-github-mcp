# Changelog

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
