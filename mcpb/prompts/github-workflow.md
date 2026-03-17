# GitHub Workflow Guidance

Use `github_ops` for GitHub operations via gh CLI. 43 actions available.
Requires: `gh auth login`

## Operation Groups

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

## Common Workflows

### Issue triage
```
github_ops(operation='issue_list', owner='sandraschi', repo='my-mcp', state='open', limit=50)
github_ops(operation='issue_comment', owner='sandraschi', repo='my-mcp', issue_number=5, body='Fixed in v0.3.0')
github_ops(operation='issue_close', owner='sandraschi', repo='my-mcp', issue_number=5)
```

### Create and merge a PR
```
github_ops(operation='pr_create', owner='sandraschi', repo='my-mcp',
           title='feat: add sampling', body='...', head_branch='feature/sampling', base_branch='master')
github_ops(operation='pr_comment', owner='sandraschi', repo='my-mcp', pr_number=3, body='LGTM')
github_ops(operation='pr_merge', owner='sandraschi', repo='my-mcp', pr_number=3, merge_method='squash')
```

### Publish a release
```
github_ops(operation='release_create', owner='sandraschi', repo='my-mcp',
           tag_name='v0.3.0', release_name='v0.3.0 — FastMCP 3.1',
           body='See CHANGELOG.md')
```

### CI/CD management
```
github_ops(operation='workflow_runs', owner='sandraschi', repo='my-mcp', limit=10)
github_ops(operation='workflow_cancel', owner='sandraschi', repo='my-mcp', run_id='12345678')
github_ops(operation='secrets_set', owner='sandraschi', repo='my-mcp',
           secret_name='PYPI_TOKEN', secret_value='pypi-...')
```

### Repo housekeeping
```
github_ops(operation='repo_rename', owner='sandraschi', repo='old-name', new_name='new-name')
github_ops(operation='repo_archive', owner='sandraschi', repo='deprecated-mcp')
github_ops(operation='label_create', owner='sandraschi', repo='my-mcp',
           label_name='glama-ready', label_color='0075ca')
```

## Key Parameters

| Param | Used by |
|-------|---------|
| owner, repo | All repo/issue/PR/release operations |
| title, body | issue_create, pr_create, release_create |
| issue_number | issue_view, issue_close, issue_comment |
| pr_number | pr_view, pr_merge, pr_close, pr_comment |
| state | issue_list, pr_list (open/closed/all) |
| limit | list operations (default: 20) |
| tag_name | release_view/create/delete/update |
| workflow_id | workflow_run/disable/enable |
| run_id | workflow_cancel |
| secret_name, secret_value | secrets_set |
| username, permission | collaborator_add |
| label_name, label_color | label_create |
| new_name | repo_rename |
| merge_method | pr_merge (merge/squash/rebase) |
| query | search_repos/issues/code |

## Agentic Workflows

For multi-step tasks, use `git_agentic_workflow` instead:
```
git_agentic_workflow(
    task="List all open bug issues, add a 'needs-triage' label to each, and create a tracking issue summary",
    owner="sandraschi",
    repo="my-mcp"
)
```
