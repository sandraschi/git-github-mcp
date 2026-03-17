# Git Workflow Guidance

Use `git_ops` for all local Git operations. 43 actions available.

## Operation Groups

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

## Common Workflows

### Standard commit flow
```
git_ops(operation='status', repo_path='.')
git_ops(operation='add', repo_path='.', all_files=True)
git_ops(operation='commit', repo_path='.', message='feat: add feature')
git_ops(operation='push', repo_path='.', remote='origin', branch='master')
```

### Feature branch
```
git_ops(operation='branch_create', repo_path='.', branch='feature/x', source_branch='master')
git_ops(operation='branch_switch', repo_path='.', branch='feature/x')
# ... make changes ...
git_ops(operation='add', repo_path='.', all_files=True)
git_ops(operation='commit', repo_path='.', message='feat(x): implement x')
git_ops(operation='push', repo_path='.', set_upstream=True, branch='feature/x')
```

### Safe cleanup
```
git_ops(operation='clean', repo_path='.', dry_run=True)   # preview
git_ops(operation='clean', repo_path='.', include_dirs=True)  # execute
```

### Debug a regression with bisect
```
git_ops(operation='bisect_start', repo_path='.')
git_ops(operation='bisect_bad', repo_path='.')          # current HEAD is bad
git_ops(operation='bisect_good', repo_path='.', commit='v0.2.0')  # known good
# git bisect will checkout commits; mark each:
git_ops(operation='bisect_bad', repo_path='.')   # or bisect_good
git_ops(operation='bisect_reset', repo_path='.')  # done
```

## Key Parameters

| Param | Used by |
|-------|---------|
| repo_path | All operations (default: cwd) |
| message | commit, branch_merge |
| files / all_files | add |
| remote, branch | push, pull, fetch |
| force | push, branch_delete, worktree_remove |
| commit, commit2 | diff, show, blame, reset, revert, cherry_pick |
| file_path | blame |
| source_branch | branch_create, branch_merge, rebase |
| mode | reset (soft/mixed/hard) |
| dry_run, include_dirs | clean |
| recursive | submodule_update, submodule_sync |
| worktree_path | worktree_add, worktree_remove |
