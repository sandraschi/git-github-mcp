"""FastMCP 2.14.4 server with git_ops and github_ops portmanteaus."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Literal

from fastmcp import FastMCP, Context

from .tools.git_ops import git_ops as _run_git_ops
from .tools.github_ops import github_ops as _run_github_ops

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
    """
    Git repository operations (portmanteau).

    FEATURES:
    - clone, status, add, commit, push, pull
    - branch, tag, stash
    - Cross-platform (pathlib)

    Args:
        operation: clone, status, add, commit, push, pull, branch, tag, stash
        repo_path: Path to repo (default: cwd)
        message: Commit message (required for commit)
        files: Files to add (for add)
        remote: Remote name (default: origin)
        branch: Branch name
        force: Force push
        all_files: Add all files
        target_dir: Clone destination (for clone)
        repo_url: Clone URL (for clone)

    Returns:
        Dialogic response with success, result, recommendations, next_steps.
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
    """
    GitHub operations via gh CLI (portmanteau).

    FEATURES:
    - create_issue, list_issues, create_pr, list_prs, search
    - Uses gh auth (no token in MCP)

    Args:
        operation: create_issue, list_issues, create_pr, list_prs, search
        owner: Repo owner (e.g. openclaw)
        repo: Repo name (e.g. openclaw)
        title: Issue/PR title
        body: Issue/PR body
        issue_number: For issue operations
        pr_number: For PR operations
        query: Search query
        state: open, closed, all
        limit: Max results

    Returns:
        Dialogic response with success, result, recommendations, next_steps.
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
