# git-github-mcp — User Guide

## Getting Started

Connect to the git-github-mcp server from any MCP-compatible client (Claude Desktop, Cursor, Windsurf, etc.). The server provides access to local Git repositories and remote GitHub operations. Start by checking system status to confirm connectivity, then explore available tools.

### Quick Start
```
git_github_status() — Verify git and gh CLI availability and authentication
git_github_help(level="basic") — See all available tools and operations
```

## Git Operations Tutorial

### Checking Repository Status

The most common Git operation is checking the status of your working tree. The status output includes staged changes, unstaged changes, untracked files, and unmerged files with structured counts.

```
git_core(operation="status", repo_path="D:/Dev/repos/my-project")
```

The response includes: branch name, remote URL, staged files (with added/modified/deleted classifications), unstaged files, untracked files, unmerged files, and summary counts.

### Making Commits

A typical commit workflow involves staging files, writing a commit message, and pushing:

```
git_core(operation="add", repo_path=".", files=["src/main.py", "src/utils.py"])
git_core(operation="commit", repo_path=".", message="feat: add user authentication")
git_core(operation="push", repo_path=".", remote="origin", branch="main")
```

For quick iteration, use all_files to stage everything:

```
git_core(operation="add", repo_path=".", all_files=True)
git_core(operation="commit", repo_path=".", message="fix: resolve login redirect bug")
git_core(operation="push", repo_path=".", remote="origin", branch="main", force=True)
```

Note: force=True uses --force-with-lease, which is safer than --force because it refuses to update a branch unless it is what you expect.

### Branch Management

Create and work with feature branches:

```
git_branch(operation="branch_create", repo_path=".", branch="feature/new-dashboard", source_branch="main")
```

List all branches to see what's available:

```
git_branch(operation="branch_list", repo_path=".")
```

Merge a completed feature back:

```
git_branch(operation="branch_switch", repo_path=".", branch="main")
git_branch(operation="branch_merge", repo_path=".", source_branch="feature/new-dashboard")
```

Delete the feature branch when done:

```
git_branch(operation="branch_delete", repo_path=".", branch="feature/new-dashboard")
```

### Stashing Work in Progress

Save uncommitted changes temporarily:

```
git_branch(operation="stash", repo_path=".", stash_message="WIP: mid-refactor")
```

View stashed changes:

```
git_branch(operation="stash_list", repo_path=".")
```

Restore the most recent stash:

```
git_branch(operation="stash_pop", repo_path=".")
```

### Viewing History

See recent commits:

```
git_core(operation="log", repo_path=".", max_count=20, oneline=True)
```

For detailed commit information:

```
git_core(operation="log", repo_path=".", max_count=10, oneline=False)
```

View changes between commits or the working tree:

```
git_core(operation="diff", repo_path=".", commit="HEAD~1", commit2="HEAD")
git_core(operation="diff", repo_path=".", files=["src/server.py"])
```

### Undoing Changes

Reset to a previous state:

```
git_admin(operation="reset", repo_path=".", mode="soft", commit="HEAD~1")
```

Available modes: soft (keep changes staged), mixed (keep changes unstaged), hard (discard changes).

Revert a specific commit with a new commit:

```
git_admin(operation="revert", repo_path=".", commit="abc1234")
```

Cherry-pick a commit from another branch:

```
git_admin(operation="cherry_pick", repo_path=".", commit="def5678")
```

### Cleaning Untracked Files

Preview what would be removed:

```
git_admin(operation="clean", repo_path=".", dry_run=True)
```

Actually remove untracked files (and directories):

```
git_admin(operation="clean", repo_path=".", include_dirs=True)
```

### Using Git Bisect

Find the commit that introduced a bug:

```
git_admin(operation="bisect_start", repo_path=".")
git_admin(operation="bisect_bad", repo_path=".")           # Current commit is bad
git_admin(operation="bisect_good", repo_path=".", commit="v1.0.0")  # Known good commit
# Continue marking bisect_bad/bisect_good until the culprit is found
git_admin(operation="bisect_reset", repo_path=".")
```

### Working with Submodules

Add a submodule:

```
git_admin(operation="submodule_add", repo_path=".", submodule_url="https://github.com/user/lib.git", submodule_path="libs/lib")
```

Update all submodules recursively:

```
git_admin(operation="submodule_update", repo_path=".", recursive=True)
```

Check submodule status:

```
git_admin(operation="submodule_status", repo_path=".")
```

### Using Worktrees

Worktrees allow checking out multiple branches simultaneously:

```
git_admin(operation="worktree_add", repo_path=".", worktree_path="../hotfix-release", branch="hotfix/urgent")
```

List all worktrees:

```
git_admin(operation="worktree_list", repo_path=".")
```

## GitHub Operations Tutorial

### Checking Authentication

Before using GitHub operations, verify the gh CLI is authenticated:

```
github_ops(operation="auth_status")
```

If not authenticated, run gh auth login in your terminal.

### Repository Management

List repositories for a user or organization:

```
github_ops(operation="repo_list", owner="sandraschi", limit=30)
```

View detailed repository information:

```
github_ops(operation="repo_view", owner="sandraschi", repo="git-github-mcp")
```

For a formatted card view:

```
github_ops(operation="show_repo", owner="sandraschi", repo="git-github-mcp", output_format="markdown")
```

Create a new repository:

```
github_ops(operation="repo_create", repo="my-new-server", description="A useful MCP server", private=False)
```

Fork a repository:

```
github_ops(operation="repo_fork", owner="someuser", repo="interesting-project")
```

### Issue Management

List open issues:

```
github_ops(operation="issue_list", owner="sandraschi", repo="git-github-mcp", state="open", limit=20)
```

Create a new issue:

```
github_ops(operation="issue_create", owner="sandraschi", repo="git-github-mcp", title="Add feature X", body="Description of the feature request")
```

Comment on an existing issue:

```
github_ops(operation="issue_comment", owner="sandraschi", repo="git-github-mcp", issue_number=5, body="I'll work on this")
```

Close an issue:

```
github_ops(operation="issue_close", owner="sandraschi", repo="git-github-mcp", issue_number=5)
```

### Pull Request Management

List open PRs:

```
github_ops(operation="pr_list", owner="sandraschi", repo="git-github-mcp", state="open")
```

Create a pull request:

```
github_ops(operation="pr_create", owner="sandraschi", repo="git-github-mcp", title="feat: add new endpoint", body="Implements API endpoint for user profiles", head_branch="feature/profiles", base_branch="main")
```

Merge a PR with different strategies:

```
github_ops(operation="pr_merge", owner="sandraschi", repo="git-github-mcp", pr_number=12, merge_method="squash")
```

Available merge methods: merge (default, preserves history), squash (single commit), rebase (linear history).

Comment on a PR:

```
github_ops(operation="pr_comment", owner="sandraschi", repo="git-github-mcp", pr_number=12, body="LGTM! Ready to merge.")
```

### Release Management

List releases:

```
github_ops(operation="release_list", owner="sandraschi", repo="git-github-mcp")
```

Create a new release:

```
github_ops(operation="release_create", owner="sandraschi", repo="git-github-mcp", tag_name="v1.0.0", release_name="v1.0.0 — Major Release", body="See CHANGELOG for details", prerelease=False)
```

Update an existing release:

```
github_ops(operation="release_update", owner="sandraschi", repo="git-github-mcp", tag_name="v1.0.0", body="Updated changelog with new fixes")
```

Delete a release:

```
github_ops(operation="release_delete", owner="sandraschi", repo="git-github-mcp", tag_name="v0.9.0-test")
```

### Actions Workflow Management

List workflows in a repository:

```
github_ops(operation="workflow_list", owner="sandraschi", repo="git-github-mcp")
```

Trigger a workflow run:

```
github_ops(operation="workflow_run", owner="sandraschi", repo="git-github-mcp", workflow_id="ci.yml", ref="main")
```

View recent workflow runs:

```
github_ops(operation="workflow_runs", owner="sandraschi", repo="git-github-mcp", limit=10)
```

Cancel a running workflow:

```
github_ops(operation="workflow_cancel", owner="sandraschi", repo="git-github-mcp", run_id="12345678")
```

Disable or enable a workflow:

```
github_ops(operation="workflow_disable", owner="sandraschi", repo="git-github-mcp", workflow_id="ci.yml")
github_ops(operation="workflow_enable", owner="sandraschi", repo="git-github-mcp", workflow_id="ci.yml")
```

### Searching GitHub

Search repositories by query:

```
github_ops(operation="search_repos", query="topic:mcp language:python", limit=20)
```

Search by GitHub topic tag:

```
github_ops(operation="search_repos_topic", topic="mcp", owner="sandraschi", limit=30)
```

Search code across repositories:

```
github_ops(operation="search_code", query="import fastmcp user:sandraschi", limit=20, pretty=True)
```

Find repos with specific file extensions:

```
github_ops(operation="code_find_repos", owner="sandraschi", extension="bak", limit=50)
```

Search issues across repositories:

```
github_ops(operation="search_issues", query="is:open label:bug repo:sandraschi/git-github-mcp", limit=10)
```

### Managing Labels

List labels for a repository:

```
github_ops(operation="label_list", owner="sandraschi", repo="git-github-mcp")
```

Create a new label with color:

```
github_ops(operation="label_create", owner="sandraschi", repo="git-github-mcp", label_name="glama-ready", label_color="0075ca", label_description="Ready for Glama publication")
```

Delete a label:

```
github_ops(operation="label_delete", owner="sandraschi", repo="git-github-mcp", label_name="deprecated")
```

### Managing Secrets

List repository secrets:

```
github_ops(operation="secrets_list", owner="sandraschi", repo="git-github-mcp")
```

Set a secret:

```
github_ops(operation="secrets_set", owner="sandraschi", repo="git-github-mcp", secret_name="DEPLOY_KEY", secret_value="your-secret-here")
```

Delete a secret:

```
github_ops(operation="secrets_delete", owner="sandraschi", repo="git-github-mcp", secret_name="DEPLOY_KEY")
```

### Managing Collaborators

Add a collaborator:

```
github_ops(operation="collaborator_add", owner="sandraschi", repo="git-github-mcp", username="teammate", permission="push")
```

Permission levels: pull (read), push (write), triage (issues), maintain, admin (full).

Remove a collaborator:

```
github_ops(operation="collaborator_remove", owner="sandraschi", repo="git-github-mcp", username="former-teammate")
```

### GitHub Projects

List Projects (v2):

```
github_ops(operation="project_list", owner="@me", limit=20)
```

View a specific project:

```
github_ops(operation="project_view", owner="@me", project_number=1)
```

Create a new project:

```
github_ops(operation="project_create", owner="@me", title="Q3 Planning", body="Track quarterly goals")
```

### GitHub Packages

List packages of a specific type:

```
github_ops(operation="package_list", package_type="npm", owner="sandraschi")
```

View a specific package:

```
github_ops(operation="package_view", package_type="npm", package_name="my-package", owner="sandraschi")
```

## Agentic Workflows

### Multi-Step Git+GitHub Tasks

Use git_agentic_workflow for complex operations that require reasoning across Git and GitHub:

```
git_agentic_workflow(task="Create a release branch from main, bump version to 1.2.0, commit the change, push the branch, and open a PR against main")
```

The server will plan and execute the steps using LLM sampling.

### GitHub Discovery Tasks

Use git_github_search_workflow for research/discovery operations:

```
git_github_search_workflow(task="Find all repos in the sandraschi org that need updates based on stale dependencies", owner="sandraschi")
```

## Fleet Maintainer Tools

### Morning Digest

Scan your fleet repositories for open PRs, issues, and notifications:

```
fleet_morning_digest(stale_days=7, include_issues=True, include_notifications=True)
```

### Full Fleet Maintainer Suite

Run all fleet checks in sequence:

```
fleet_ops(operation="full_suite")
```

Individual operations:

```
fleet_ops(operation="registry_load")       # Load fleet registry
fleet_ops(operation="port_audit")          # Check port assignments
fleet_ops(operation="ci_pulse")            # CI health check
fleet_ops(operation="dependabot_digest")   # Dependabot alerts
fleet_ops(operation="grade_snapshot")      # Grade snapshots
```

## Gitingest Integration

Generate LLM-ready repo digest URLs:

```
github_ops(operation="gitingest_link", owner="sandraschi", repo="git-github-mcp")
github_ops(operation="gitingest_link", owner="sandraschi", repo="git-github-mcp", ref="main", subpath="src")
github_ops(operation="gitingest_convert_url", github_url="https://github.com/sandraschi/git-github-mcp")
github_ops(operation="gitingest_help")
```

## Troubleshooting

### Git Not Found
If git operations fail with "not found", ensure Git is installed at C:\Program Files\Git\bin\git.exe or update the _GIT_EXE path in tools/git_ops.py.

### gh CLI Not Authenticated
Run github_ops(operation="auth_status") to check authentication. If not authenticated, run gh auth login in your terminal. For CI/automation, set GH_TOKEN environment variable.

### Subprocess Hangs
If a Git operation hangs, the server has a 180-second timeout for network operations (clone, push, pull, fetch) and 25 seconds for local operations. Timeout errors include recovery options. Restart the server if it becomes unresponsive.

### Permission Denied
For repository operations, ensure you have the required access level. GitHub operations require appropriate scopes: repo for private repos, read:packages for packages, project for Projects v2. Run gh auth refresh -s <scope> to add missing scopes.

### Web Dashboard Unreachable
Ensure the HTTP bridge is running on port 10702. Check that no other process is using the port. Start the server with MCP_TRANSPORT=http if you need explicit HTTP mode.
