"""FastMCP 2.14.4 server with git_ops and github_ops portmanteaus."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Literal

from fastmcp import FastMCP, Context

from .tools.git_ops import git_ops as _run_git_ops
from .tools.github_ops import github_ops as _run_github_ops
from .tools.help import get_help as _run_help
from .tools.status import get_status as _run_status

logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")
logger = logging.getLogger("git-github-mcp")


@asynccontextmanager
async def server_lifespan(mcp_instance: FastMCP):
    """Server lifespan for startup and cleanup."""
    logger.info("git-github-mcp starting")
    yield
    logger.info("git-github-mcp shutting down")


mcp = FastMCP(
    "git-github-mcp",
    version="0.1.0",
    lifespan=server_lifespan,
)


@mcp.tool()
async def git_ops(
    operation: Literal["clone", "status", "add", "commit", "push", "pull", "branch", "tag", "stash"],
    repo_path: str | None = None,
    message: str | None = None,
    files: list[str] | None = None,
    remote: str = "origin",
    branch: str | None = None,
    force: bool = False,
    all_files: bool = False,
    target_dir: str | None = None,
    repo_url: str | None = None,
    ctx: Context | None = None,
) -> dict:
    """Git repository operations (portmanteau). Local Git via subprocess.

    SUPPORTED OPERATIONS:
    - clone: Clone a repository (requires repo_url)
    - status: Check branch, staged/unstaged changes
    - add: Stage files for commit
    - commit: Create commit (requires message)
    - push: Push to remote
    - pull: Pull from remote
    - branch: List branches
    - tag: List tags
    - stash: List stashes

    OPERATIONS DETAIL:

    clone: Clone a Git repository
    - Parameters: repo_url (required), target_dir (optional)
    - Returns: Cloned path and next steps
    - Example: git_ops(operation='clone', repo_url='https://github.com/owner/repo.git')

    status: Show working tree status
    - Parameters: repo_path (optional, default: cwd)
    - Returns: Current branch and short status
    - Example: git_ops(operation='status', repo_path='.')

    add: Stage files for commit
    - Parameters: files (list) or all_files=True, repo_path (optional)
    - Returns: Staged file count
    - Example: git_ops(operation='add', repo_path='.', files=['src/main.py'])

    commit: Record changes to the repository
    - Parameters: message (required), repo_path (optional), all_files (optional)
    - Returns: Commit output
    - Example: git_ops(operation='commit', repo_path='.', message='Fix bug')

    push: Push to remote
    - Parameters: repo_path, remote (default: origin), branch, force (optional)
    - Returns: Push confirmation
    - Example: git_ops(operation='push', repo_path='.', remote='origin')

    pull: Pull from remote
    - Parameters: repo_path, remote, branch (optional)
    - Returns: Pull output

    branch, tag, stash: List branches/tags/stashes
    - Parameters: repo_path (optional)

    Args:
        operation: One of clone, status, add, commit, push, pull, branch, tag, stash
        repo_path: Path to repo (default: current directory)
        message: Commit message (required for commit)
        files: Files to stage (for add; use all_files=True for all)
        remote: Remote name (default: origin)
        branch: Branch name for push/pull
        force: Force push (default: False)
        all_files: Stage all files (for add) or commit all (for commit)
        target_dir: Clone destination directory
        repo_url: Repository URL (required for clone)

    Returns:
        Dictionary with success, result, message, next_steps, execution_time_ms.
        On error: success=False, error, recovery_options.

    Examples:
        git_ops(operation='clone', repo_url='https://github.com/owner/repo.git')
        git_ops(operation='status', repo_path='D:/Dev/repos/my-repo')
        git_ops(operation='add', repo_path='.', files=['file.py'], all_files=False)
        git_ops(operation='commit', repo_path='.', message='Fix typo')
        git_ops(operation='push', repo_path='.', remote='origin', branch='main')

    Notes:
        - Cross-platform (pathlib). repo_path accepts Windows and Unix paths.
        - If push fails, run gh auth login. Use force=True for force push.
    """
    start = time.perf_counter()
    if ctx:
        ctx.info("git_ops", operation=operation)
    result = _run_git_ops(
        operation=operation,
        repo_path=repo_path,
        message=message,
        files=files,
        remote=remote,
        branch=branch,
        force=force,
        all_files=all_files,
        target_dir=target_dir,
        repo_url=repo_url,
    )
    result["execution_time_ms"] = (time.perf_counter() - start) * 1000
    return result


@mcp.tool()
async def github_ops(
    operation: Literal["create_issue", "list_issues", "create_pr", "list_prs", "search"],
    owner: str | None = None,
    repo: str | None = None,
    title: str | None = None,
    body: str | None = None,
    issue_number: int | None = None,
    pr_number: int | None = None,
    query: str | None = None,
    state: str = "open",
    limit: int = 10,
    ctx: Context | None = None,
) -> dict:
    """GitHub operations via gh CLI (portmanteau). Requires gh auth login.

    SUPPORTED OPERATIONS:
    - create_issue: Create a new issue
    - list_issues: List issues (open/closed/all)
    - create_pr: Create a pull request
    - list_prs: List pull requests
    - search: Search repositories (GitHub search syntax)

    OPERATIONS DETAIL:

    create_issue: Create a new GitHub issue
    - Parameters: owner, repo, title (required), body (optional)
    - Returns: Issue URL and title
    - Example: github_ops(operation='create_issue', owner='x', repo='y', title='Bug', body='...')

    list_issues: List issues in a repository
    - Parameters: owner, repo (required), state (default: open), limit (default: 10)
    - Returns: List of issues with number, title, state, url
    - Example: github_ops(operation='list_issues', owner='sandraschi', repo='git-github-mcp')

    create_pr: Create a pull request
    - Parameters: owner, repo, title (required), body (optional)
    - Returns: PR URL and title
    - Example: github_ops(operation='create_pr', owner='x', repo='y', title='Feature', body='...')

    list_prs: List pull requests
    - Parameters: owner, repo (required), state (default: open), limit (default: 10)
    - Returns: List of PRs with number, title, state, url

    search: Search GitHub repositories
    - Parameters: query (required), limit (default: 10)
    - Returns: Matching repos with name, fullName, description, url
    - Example: github_ops(operation='search', query='mcp server language:python', limit=10)

    Args:
        operation: One of create_issue, list_issues, create_pr, list_prs, search
        owner: Repository owner (required for issue/PR operations)
        repo: Repository name (required for issue/PR operations)
        title: Issue or PR title (required for create_issue, create_pr)
        body: Issue or PR body (optional)
        query: Search query (required for search; GitHub search syntax)
        state: open, closed, or all (default: open)
        limit: Maximum results (default: 10)

    Returns:
        Dictionary with success, result, message, next_steps, execution_time_ms.
        On error: success=False, error, recovery_options.

    Examples:
        github_ops(operation='list_issues', owner='sandraschi', repo='git-github-mcp')
        github_ops(operation='create_issue', owner='x', repo='y', title='Bug report', body='...')
        github_ops(operation='list_prs', owner='x', repo='y', state='open', limit=5)
        github_ops(operation='search', query='mcp in:name', limit=10)

    Notes:
        - Requires gh CLI installed and authenticated (gh auth login).
        - Set GITHUB_TOKEN env var if needed for automation.
        - Search uses GitHub search syntax (e.g. language:python, org:owner).
    """
    start = time.perf_counter()
    if ctx:
        ctx.info("github_ops", operation=operation)
    result = _run_github_ops(
        operation=operation,
        owner=owner,
        repo=repo,
        title=title,
        body=body,
        issue_number=issue_number,
        pr_number=pr_number,
        query=query,
        state=state,
        limit=limit,
    )
    result["execution_time_ms"] = (time.perf_counter() - start) * 1000
    return result


@mcp.tool()
async def mcp_help(level: str = "basic", topic: str | None = None, ctx: Context | None = None) -> dict:
    """Contextual help for git-github-mcp tools.

    SUPPORTED OPERATIONS:
    - level: basic | intermediate | advanced
    - topic: git_ops | github_ops | None (overview)

    LEVELS:
    - basic: Quick reference and common workflows
    - intermediate: Full operation list with parameters
    - advanced: Examples, error handling, recovery

    Args:
        level: Help detail level (basic, intermediate, advanced)
        topic: Focus on git_ops, github_ops, or None for overview

    Returns:
        Dictionary with success, result.help_content, level, topic.

    Examples:
        mcp_help() - Basic overview
        mcp_help(level='intermediate') - Full parameter reference
        mcp_help(level='advanced', topic='git_ops') - Git examples and recovery
    """
    if ctx:
        ctx.info("help", level=level, topic=topic)
    return _run_help(level=level, topic=topic)


@mcp.tool()
async def status(level: str = "basic", ctx: Context | None = None) -> dict:
    """Report system status: git and gh CLI availability.

    LEVELS:
    - basic: git/gh availability, versions, auth status
    - detailed: + platform, Python version

    Args:
        level: basic or detailed

    Returns:
        Dictionary with success, result (git, gh, tools).
        On error: success=False if git or gh not found.

    Examples:
        status() - Basic availability check
        status(level='detailed') - Full system info
    """
    if ctx:
        ctx.info("status", level=level)
    return _run_status(level=level)
