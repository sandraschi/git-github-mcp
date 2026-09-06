"""git-github-mcp server — FastMCP 3.1+, portmanteau pattern.

Tools:     git_ops (43), github_ops (58), git_github_status, git_github_help,
           git_agentic_workflow, git_github_search_workflow (sampling / agentic)
Resources: git://repo/*, github://owner/repo/*, git://skills/*
Prompts:   git_commit_message, git_release_notes, git_pr_description,
           git_review_diff, github_issue_template, github_debug_workflow,
           git_github_explain_concept
Web:       FastAPI bridge (e.g. POST /api/git, /api/github, /api/discovery)
"""

import asyncio
import json
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastmcp import Context, FastMCP
from fastmcp.server import create_proxy
from fastmcp.tools import ToolResult

from .activity_log import install_log_handler, log_activity
from .capabilities import build_capabilities
from .logs_api import build_router as _build_logs_router
from .services.fleet_ops import fleet_ops as _fleet_ops
from .services.fleet_orchestrator import run_full_suite as _run_full_suite
from .services.morning_digest import run_morning_digest as _run_morning_digest
from .tools.git_ops import git_ops as _git_ops
from .tools.github_ops import github_ops as _github_ops
from .tools.help import get_help as _get_help
from .tools.status import get_status as _get_status
from .utils import destructive_gate
from .web_discovery import PRESETS as DISCOVERY_PRESETS
from .web_discovery import run_discovery_workflow as _run_discovery_workflow

logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")
logger = logging.getLogger("git-github-mcp")
install_log_handler()

VERSION = "0.5.0"

_READ_ONLY = {"readonly": True}
_MUTATING = {}
WEB_PORT = int(os.getenv("WEB_PORT", "10713"))
WEB_HOST = os.getenv("WEB_HOST", "127.0.0.1")
_START_TIME = time.time()


@asynccontextmanager
async def server_lifespan(mcp_instance: FastMCP):
    logger.info(f"git-github-mcp v{VERSION} starting (FastMCP 3.1+)")
    yield
    logger.info("git-github-mcp shutting down")


mcp = FastMCP(
    "git-github-mcp",
    version=VERSION,
    lifespan=server_lifespan,
    instructions=(
        "Git and GitHub operations server. "
        "Use git_core for status/log/diff/commit/push/pull/fetch (11 ops). "
        "Use git_branch for branches/merge/rebase/stash/tag (14 ops). "
        "Use git_admin for remote/reset/clean/submodule/bisect (16 ops). "
        "Use git_blame for file blame (1 op). "
        "Use git_github_help for full operation reference. "
        "Use git_agentic_workflow for multi-step operations that require reasoning. "
        "Use git_github_search_workflow for agentic GitHub discovery/search tasks. "
        "Use fleet_morning_digest for daily PR/issue/notification breakfast summary across fleet repos. "
        "Use fleet_ops for full maintainer toolkit (registry_load, port_audit, ci_pulse, full_suite, etc.)."
    ),
)

_bridge_proxies = []
bridge_urls = os.getenv("MCP_BRIDGE_URLS", "")
if bridge_urls:
    for url in bridge_urls.split(","):
        url = url.strip()
        if url:
            try:
                mcp.add_provider(create_proxy(url))
                _bridge_proxies.append(url)
            except Exception:
                logger.debug("Bridge proxy failed for %s", url)


# ── Tools ─────────────────────────────────────────────────────────────────────


CORE_OPS = {"init", "clone", "add", "commit", "push", "pull", "fetch", "status", "log", "diff", "show"}
BRANCH_OPS = {
    "branch_list",
    "branch_create",
    "branch_switch",
    "branch_delete",
    "branch_rename",
    "branch_merge",
    "rebase",
    "stash",
    "stash_pop",
    "stash_list",
    "stash_drop",
    "tag_list",
    "tag_create",
    "tag_delete",
}
ADMIN_OPS = {
    "remote_list",
    "remote_add",
    "remote_remove",
    "reset",
    "revert",
    "cherry_pick",
    "clean",
    "submodule_add",
    "submodule_update",
    "submodule_sync",
    "submodule_status",
    "bisect_start",
    "bisect_bad",
    "bisect_good",
    "bisect_reset",
    "worktree_add",
    "worktree_list",
    "worktree_remove",
}
BLAME_OPS = {"blame"}


async def _run_git_tool(
    operation: str,
    repo_path: str | None = None,
    message: str | None = None,
    files: list[str] | None = None,
    all_files: bool = False,
    amend: bool = False,
    remote: str = "origin",
    branch: str | None = None,
    force: bool = False,
    set_upstream: bool = False,
    repo_url: str | None = None,
    target_dir: str | None = None,
    initial_branch: str = "main",
    depth: int | None = None,
    max_count: int = 20,
    commit: str | None = None,
    commit2: str | None = None,
    oneline: bool = False,
    file_path: str | None = None,
    source_branch: str | None = None,
    stash_message: str | None = None,
    stash_index: int = 0,
    tag_name: str | None = None,
    tag_message: str | None = None,
    mode: str = "mixed",
    remote_url: str | None = None,
    remote_name: str | None = None,
    dry_run: bool = False,
    include_dirs: bool = False,
    submodule_url: str | None = None,
    submodule_path: str | None = None,
    recursive: bool = False,
    worktree_path: str | None = None,
) -> dict:
    """Run git_ops (async) with an operation-aware timeout to catch hangs before the MCP client does."""
    # Network ops (clone, push, pull, fetch) can be slow on large repos; local ops keep 25s.
    _NETWORK_OPS = {"clone", "push", "pull", "fetch"}
    _wall_timeout = 180 if operation in _NETWORK_OPS else 25
    start = time.perf_counter()
    try:
        result = await asyncio.wait_for(
            _git_ops(
                operation=operation,
                repo_path=repo_path,
                message=message,
                files=files,
                all_files=all_files,
                amend=amend,
                remote=remote,
                branch=branch,
                force=force,
                set_upstream=set_upstream,
                repo_url=repo_url,
                target_dir=target_dir,
                initial_branch=initial_branch,
                depth=depth,
                max_count=max_count,
                commit=commit,
                commit2=commit2,
                oneline=oneline,
                file_path=file_path,
                source_branch=source_branch,
                stash_message=stash_message,
                stash_index=stash_index,
                tag_name=tag_name,
                tag_message=tag_message,
                mode=mode,
                remote_url=remote_url,
                remote_name=remote_name,
                dry_run=dry_run,
                include_dirs=include_dirs,
                submodule_url=submodule_url,
                submodule_path=submodule_path,
                recursive=recursive,
                worktree_path=worktree_path,
            ),
            timeout=_wall_timeout,
        )
    except TimeoutError:
        from .utils.response import error_response

        result = error_response(
            operation=operation,
            error=f"Git subprocess did not respond in {_wall_timeout}s",
            recovery_options=[
                "Restart the git-github-mcp server",
                "Connect via HTTP: http://127.0.0.1:10713/mcp",
                "Check that git works: git status",
            ],
            suggested_fixes=[
                "Use git_core via the REST API at http://127.0.0.1:10713/api/git",
                "Set MCP_TRANSPORT=http and connect to port 10713",
            ],
        )
    except Exception as exc:
        from .utils.response import error_response

        result = error_response(
            operation=operation,
            error=str(exc),
            recovery_options=["Check server logs", "Restart the MCP server"],
        )
    result["execution_time_ms"] = round((time.perf_counter() - start) * 1000, 2)
    return result


@mcp.tool(annotations=_MUTATING)
async def git_core(
    operation: str,
    repo_path: str | None = None,
    message: str | None = None,
    files: list[str] | None = None,
    all_files: bool = False,
    amend: bool = False,
    remote: str = "origin",
    branch: str | None = None,
    force: bool = False,
    set_upstream: bool = False,
    repo_url: str | None = None,
    target_dir: str | None = None,
    initial_branch: str = "main",
    depth: int | None = None,
    max_count: int = 20,
    commit: str | None = None,
    commit2: str | None = None,
    oneline: bool = False,
    file_path: str | None = None,
    confirm: bool = False,
) -> dict:
    """Git core operations — status, log, diff, show, init, clone, add, commit, push, pull, fetch.

    Core workflow tools. For branch/tag/stash operations use git_branch.
    For remote/reset/clean/submodule/bisect/worktree use git_admin.
    Force-push/pull/fetch/clone need confirm=True (red-shelf gate).
    """
    if operation not in CORE_OPS:
        from .utils.response import error_response

        return error_response(
            operation,
            f"Unknown operation '{operation}'. Valid: {sorted(CORE_OPS)}",
            recovery_options=["Use one of the listed operations"],
        )
    refusal = destructive_gate.gate("git_core", operation, confirm=confirm, force=force)
    if refusal is not None:
        return refusal
    return await _run_git_tool(
        operation=operation,
        repo_path=repo_path,
        message=message,
        files=files,
        all_files=all_files,
        amend=amend,
        remote=remote,
        branch=branch,
        force=force,
        set_upstream=set_upstream,
        repo_url=repo_url,
        target_dir=target_dir,
        initial_branch=initial_branch,
        depth=depth,
        max_count=max_count,
        commit=commit,
        commit2=commit2,
        oneline=oneline,
        file_path=file_path,
    )


@mcp.tool(annotations=_MUTATING)
async def git_branch(
    operation: str,
    repo_path: str | None = None,
    branch: str | None = None,
    source_branch: str | None = None,
    message: str | None = None,
    force: bool = False,
    stash_message: str | None = None,
    stash_index: int = 0,
    tag_name: str | None = None,
    tag_message: str | None = None,
    confirm: bool = False,
) -> dict:
    """Git branch operations — branch lifecycle, merge, rebase, stash, tag.

    For core operations (status, log, commit, push) use git_core.
    For admin operations (remote, reset, clean, submodule) use git_admin.
    branch_delete needs confirm=True (red-shelf gate).
    """
    if operation not in BRANCH_OPS:
        from .utils.response import error_response

        return error_response(
            operation,
            f"Unknown operation '{operation}'. Valid: {sorted(BRANCH_OPS)}",
            recovery_options=["Use one of the listed operations"],
        )
    candidates = None
    if operation == "branch_delete":
        try:
            listed = await _run_git_tool(operation="branch_list", repo_path=repo_path)
            candidates = listed if isinstance(listed, dict) else None
        except Exception:
            candidates = None
    refusal = destructive_gate.gate("git_branch", operation, confirm=confirm, candidates=candidates)
    if refusal is not None:
        return refusal
    return await _run_git_tool(
        operation=operation,
        repo_path=repo_path,
        branch=branch,
        source_branch=source_branch,
        message=message,
        force=force,
        stash_message=stash_message,
        stash_index=stash_index,
        tag_name=tag_name,
        tag_message=tag_message,
    )


@mcp.tool(annotations=_MUTATING)
async def git_admin(
    operation: str,
    repo_path: str | None = None,
    remote: str = "origin",
    remote_url: str | None = None,
    remote_name: str | None = None,
    mode: str = "mixed",
    commit: str | None = None,
    force: bool = False,
    dry_run: bool = False,
    include_dirs: bool = False,
    submodule_url: str | None = None,
    submodule_path: str | None = None,
    recursive: bool = False,
    worktree_path: str | None = None,
    confirm: bool = False,
) -> dict:
    """Git admin operations — remote, reset, revert, cherry-pick, clean, submodule, bisect, worktree.

    For core operations (status, log, commit, push) use git_core.
    For branch operations use git_branch.
    reset/clean/worktree_remove need confirm=True (red-shelf gate).
    """
    if operation not in ADMIN_OPS:
        from .utils.response import error_response

        return error_response(
            operation,
            f"Unknown operation '{operation}'. Valid: {sorted(ADMIN_OPS)}",
            recovery_options=["Use one of the listed operations"],
        )
    candidates = None
    if operation == "worktree_remove":
        try:
            listed = await _run_git_tool(operation="worktree_list", repo_path=repo_path)
            candidates = listed if isinstance(listed, dict) else None
        except Exception:
            candidates = None
    refusal = destructive_gate.gate("git_admin", operation, confirm=confirm, candidates=candidates)
    if refusal is not None:
        return refusal
    return await _run_git_tool(
        operation=operation,
        repo_path=repo_path,
        remote=remote,
        remote_url=remote_url,
        remote_name=remote_name,
        mode=mode,
        commit=commit,
        force=force,
        dry_run=dry_run,
        include_dirs=include_dirs,
        submodule_url=submodule_url,
        submodule_path=submodule_path,
        recursive=recursive,
        worktree_path=worktree_path,
    )


@mcp.tool(annotations=_READ_ONLY)
async def git_blame(
    repo_path: str | None = None,
    file_path: str | None = None,
    commit: str | None = None,
) -> dict:
    """Git blame — show blame info for a file.

    Args:
        repo_path: Repository path (default: current directory).
        file_path: File to blame.
        commit: Starting commit (default: HEAD).
    """
    if not file_path:
        from .utils.response import error_response

        return error_response(
            "blame",
            "file_path is required for git blame",
            recovery_options=["Provide a file_path parameter"],
            suggested_fixes=['git_blame(file_path="src/main.py")'],
        )
    return await _run_git_tool(
        operation="blame",
        repo_path=repo_path,
        file_path=file_path,
        commit=commit,
    )


@mcp.tool(annotations=_MUTATING)
async def github_ops(
    operation: str,
    owner: str | None = None,
    repo: str | None = None,
    title: str | None = None,
    body: str | None = None,
    issue_number: int | None = None,
    pr_number: int | None = None,
    state: str = "open",
    limit: int = 20,
    label: str | None = None,
    assignee: str | None = None,
    description: str | None = None,
    private: bool = False,
    new_name: str | None = None,
    base_branch: str | None = None,
    head_branch: str | None = None,
    draft: bool = False,
    merge_method: str = "merge",
    tag_name: str | None = None,
    release_name: str | None = None,
    prerelease: bool = False,
    query: str | None = None,
    workflow_id: str | None = None,
    run_id: str | None = None,
    ref: str | None = None,
    target_dir: str | None = None,
    secret_name: str | None = None,
    secret_value: str | None = None,
    username: str | None = None,
    permission: str = "push",
    label_name: str | None = None,
    label_color: str | None = None,
    label_description: str | None = None,
    output_format: str = "markdown",
    topic: str | None = None,
    extension: str | None = None,
    path_pattern: str | None = None,
    search_scope: str | None = None,
    pretty: bool = False,
    project_number: int | None = None,
    package_type: str | None = None,
    package_name: str | None = None,
    subpath: str | None = None,
    github_url: str | None = None,
    confirm: bool = False,
) -> dict:
    """GitHub operations via gh CLI — 66 actions. Requires: gh auth login.

    REPOS:         repo_list, repo_view, show_repo, repo_create, repo_fork, repo_clone,
                   repo_delete, repo_rename, repo_archive
    ISSUES:        issue_list, issue_view, issue_create, issue_close, issue_comment
    PRs:           pr_list, pr_view, pr_create, pr_merge, pr_checkout, pr_close, pr_comment
    RELEASES:      release_list, release_view, release_create, release_delete, release_update
    ACTIONS:       workflow_list, workflow_run, workflow_runs,
                   workflow_cancel, workflow_disable, workflow_enable
    LABELS:        label_list, label_create, label_delete
    SECRETS:       secrets_list, secrets_set, secrets_delete
    COLLABORATORS: collaborator_add, collaborator_remove
    SEARCH:        search_repos, search_repos_topic, search_issues, search_code (pretty=),
                   code_find_repos
    PROJECTS:      project_list, project_view, project_create, project_delete, project_edit
    PACKAGES:      package_list, package_view, package_delete
    GITINGEST:     gitingest_link, gitingest_convert_url, gitingest_help
    MISC:          auth_status, gist_list

    Non-blocking: subprocess runs in thread pool, never freezes MCP server.
    repo_delete/release_delete need confirm=True (red-shelf gate).
    """
    refusal = destructive_gate.gate("github_ops", operation, confirm=confirm)
    if refusal is not None:
        return refusal
    start = time.perf_counter()
    result = await asyncio.to_thread(
        _github_ops,
        operation=operation,
        owner=owner,
        repo=repo,
        title=title,
        body=body,
        issue_number=issue_number,
        pr_number=pr_number,
        state=state,
        limit=limit,
        label=label,
        assignee=assignee,
        description=description,
        private=private,
        new_name=new_name,
        base_branch=base_branch,
        head_branch=head_branch,
        draft=draft,
        merge_method=merge_method,
        tag_name=tag_name,
        release_name=release_name,
        prerelease=prerelease,
        query=query,
        workflow_id=workflow_id,
        run_id=run_id,
        ref=ref,
        target_dir=target_dir,
        secret_name=secret_name,
        secret_value=secret_value,
        username=username,
        permission=permission,
        label_name=label_name,
        label_color=label_color,
        label_description=label_description,
        output_format=output_format,
        topic=topic,
        extension=extension,
        path_pattern=path_pattern,
        search_scope=search_scope,
        pretty=pretty,
        project_number=project_number,
        package_type=package_type,
        package_name=package_name,
        subpath=subpath,
        github_url=github_url,
    )
    result["execution_time_ms"] = round((time.perf_counter() - start) * 1000, 2)
    return result


@mcp.tool(annotations=_READ_ONLY)
async def fleet_morning_digest(
    fleet_repos: str | None = None,
    fleet_repos_file: str | None = None,
    stale_days: int = 7,
    include_issues: bool = True,
    include_notifications: bool = True,
    limit_per_repo: int = 30,
    maintainer_login: str | None = None,
    deliver: str | None = None,
    output_file: str | None = None,
    since_last_run: bool = True,
) -> dict:
    """Breakfast runner: scan fleet repos for open PRs/issues, stale threads, and new notifications.

    Fleet list format (one per line): owner/repo — same as web /inbox fleet mode.
    Sources: fleet_repos parameter, GIT_GITHUB_FLEET_REPOS_FILE, or config/fleet-repos.txt.

    deliver: comma-separated optional sinks — file, aiwatcher, robofang
    (or set GIT_GITHUB_DIGEST_DELIVER). Schedule via scripts/install_morning_task.ps1.

    Requires: gh auth login. Non-blocking (runs in thread pool).
    """
    start = time.perf_counter()
    result = await asyncio.to_thread(
        _run_morning_digest,
        fleet_repos=fleet_repos,
        fleet_repos_file=fleet_repos_file,
        stale_days=stale_days,
        include_issues=include_issues,
        include_notifications=include_notifications,
        limit_per_repo=limit_per_repo,
        maintainer_login=maintainer_login,
        deliver=deliver,
        output_file=output_file,
        since_last_run=since_last_run,
    )
    result["execution_time_ms"] = round((time.perf_counter() - start) * 1000, 2)
    return result


@mcp.tool(annotations=_MUTATING)
async def fleet_ops(
    operation: str,
    fleet_repos: str | None = None,
    fleet_repos_file: str | None = None,
    use_registry: bool = True,
    stale_days: int = 7,
    maintainer_login: str | None = None,
    deliver: str | None = None,
    since_last_run: bool = True,
    hours: int = 48,
    days: int = 7,
    owner: str | None = None,
    registry_path: str | None = None,
    repos_root: str | None = None,
    scraper_url: str | None = None,
    template: str | None = None,
) -> dict:
    """Fleet maintainer portmanteau for sandraschi MCP fleet.

    Operations: registry_load, port_audit, docs_gate, quarantine_report,
    ci_pulse, dependabot_digest, mention_inbox, ack_drafts, local_dirty,
    release_drift, grade_snapshot, gitingest_bundle, runner_status,
    weekly_retro, council_payload, full_suite.

    full_suite runs morning_digest plus all checks and returns a combined payload.
    Requires gh auth for GitHub-backed ops. Non-blocking (thread pool).
    """
    start = time.perf_counter()
    result = await asyncio.to_thread(
        _fleet_ops,
        operation,
        fleet_repos=fleet_repos,
        fleet_repos_file=fleet_repos_file,
        use_registry=use_registry,
        stale_days=stale_days,
        maintainer_login=maintainer_login,
        deliver=deliver,
        since_last_run=since_last_run,
        hours=hours,
        days=days,
        owner=owner,
        registry_path=registry_path,
        repos_root=repos_root,
        scraper_url=scraper_url,
        template=template,
    )
    result["execution_time_ms"] = round((time.perf_counter() - start) * 1000, 2)
    return result


@mcp.tool(annotations=_READ_ONLY)
async def git_github_status(level: str = "basic") -> dict:
    """System status: git and gh CLI availability, versions, and GitHub login state.

    Use this to confirm **GitHub CLI authentication** before relying on `github_ops` or the
    web dashboard. Checks `gh --version` and `gh auth status` (same credentials as your
    interactive terminal if the MCP server runs as your user).

    Returns:
        result.git / result.gh (version, available). When gh is installed, result.gh.auth
        is either 'ok' or 'not logged in'. If auth is missing, the response is still
        success=True with a clear message and recovery steps (install is different from
        not-logged-in — see error vs message).
    """
    return await asyncio.to_thread(_get_status, level=level)


@mcp.tool(app=True, annotations=_READ_ONLY)
async def show_status_card() -> ToolResult:
    """Show git/gh system health as a rich Prefab card in chat.

    Use this to visualise whether git and gh CLI are available,
    authenticated, and ready for use. Renders a structured card
    with status indicators, not raw JSON.
    """
    status = await asyncio.to_thread(_get_status, level="detailed")
    git = status.get("git", {})
    gh = status.get("gh", {})
    git_ok = bool(git.get("available", False))
    gh_ok = bool(gh.get("available", False))
    gh_auth = gh.get("auth") == "ok"
    platform = f"{status.get('platform', '?')} {status.get('platform_release', '')}".strip()
    text = "\n".join(
        [
            f"git: {'OK' if git_ok else 'MISSING'}",
            f"gh:  {'OK' if gh_ok else 'MISSING'}",
            f"auth: {'OK' if gh_auth else 'LOGIN REQUIRED'}" if gh_ok else "auth: n/a",
            f"platform: {platform}",
        ]
    )
    try:
        from prefab_ui import PrefabApp
        from prefab_ui.components import Row, Text

        with PrefabApp(title="Git GitHub Status") as app:
            Row(children=[Text(content="git CLI"), Text(content="Detected" if git_ok else "Not found")])
            Row(children=[Text(content="gh CLI"), Text(content="Detected" if gh_ok else "Not found")])
            if gh_ok:
                Row(
                    children=[
                        Text(content="gh auth"),
                        Text(content="Authenticated" if gh_auth else "Not logged in"),
                    ]
                )
            Row(children=[Text(content="Platform"), Text(content=platform)])
        return ToolResult(content=text, structured_content=app)
    except ImportError:
        return ToolResult(content=text)


async def _gate_plan_step(tool_name: str | None, args: dict) -> tuple[dict, dict | None]:
    """Red-shelf check for one planned workflow step.

    Pops `confirm` (implementations don't accept it), resolves the wrapper
    family from the operation, lists candidates best-effort for deletes.
    Returns (clean_args, refusal_or_None). Unknown tools and read-only ops
    pass through with (args, None).
    """
    args = dict(args or {})
    confirm = args.pop("confirm", False)
    op = str(args.get("operation") or "")
    family: str | None = None
    if tool_name == "github_ops":
        family = "github_ops"
    elif tool_name == "git_ops":
        if op in CORE_OPS:
            family = "git_core"
        elif op in BRANCH_OPS:
            family = "git_branch"
        elif op in ADMIN_OPS:
            family = "git_admin"
    if family is None:
        return args, None
    candidates = None
    if op in ("worktree_remove", "branch_delete"):
        try:
            listed = await _git_ops(
                operation="worktree_list" if op == "worktree_remove" else "branch_list",
                repo_path=args.get("repo_path"),
            )
            candidates = listed if isinstance(listed, dict) else None
        except Exception:
            candidates = None
    refusal = destructive_gate.gate(
        family, op, confirm=bool(confirm), force=bool(args.get("force", False)), candidates=candidates
    )
    return args, refusal


@mcp.tool(annotations=_READ_ONLY)
async def git_github_help(level: str = "basic", topic: str | None = None) -> dict:
    """Contextual help for git-github-mcp tools and operations.

    level: basic | intermediate | advanced
    topic: git_ops | github_ops | None (all)
    """
    return _get_help(level=level, topic=topic)


@mcp.tool(annotations=_MUTATING)
async def git_agentic_workflow(
    task: str,
    repo_path: str | None = None,
    owner: str | None = None,
    repo: str | None = None,
    ctx: Context | None = None,
) -> dict:
    """Agentic multi-step Git/GitHub workflow using LLM sampling.

    Describe a high-level task in natural language. The tool reasons about
    the required steps, executes them via git_ops/github_ops, and returns
    a structured result with the plan and outcome.

    Examples:
      task="Create a release branch from main, bump version, and open a PR"
      task="List all open issues tagged 'bug' and create a summary"
      task="Check repo status, stage all changes, commit and push"
    """
    if ctx is None:
        return {
            "success": False,
            "error": "Context not available — sampling requires an active MCP session",
        }

    await ctx.info(f"git_agentic_workflow: planning task: {task}")

    repo_ctx = f"repo_path={repo_path}" if repo_path else "repo_path=. (cwd)"
    gh_ctx = f"owner={owner}, repo={repo}" if owner and repo else "no GitHub repo specified"

    plan_prompt = f"""You are a Git/GitHub operations planner. Given a task, output a JSON plan.

Available tools:
- git_ops(operation, repo_path, ...): 43 local git actions (init, clone, status, add,
  commit, push, pull, fetch, log, diff, show, blame, branch lifecycle, rebase, remote,
  stash, tag, reset, revert, cherry_pick, submodule_*, bisect_*, worktree_*, clean).
- github_ops(operation, owner, repo, ...): 58 GitHub actions via gh CLI:
  repos (list/view/create/fork/clone/delete/rename/archive),
  issues (list/view/create/close/comment), PRs (list/view/create/merge/checkout/close/comment),
  releases (full CRUD), Actions workflows (list/run/runs/cancel/enable/disable),
  labels, secrets, collaborators,
  search (search_repos, search_repos_topic, search_issues, search_code with pretty=,
  code_find_repos for extension/path-scoped hunts),
  Projects (project_*), Packages (package_*),
   Gitingest helpers (gitingest_link, gitingest_convert_url with github_url, gitingest_help;
   optional ref, subpath on link),
   auth_status, gist_list.

Red shelf (a step using these without confirm=true returns
confirmation_required and stops the plan): worktree_remove, clean, reset,
branch_delete, force push/pull/fetch/clone, repo_delete, release_delete.
List first (worktree_list/branch_list), demand precision in args, confirm
with exact identifiers — adjectives are not identifiers.

Context:
- {repo_ctx}
- {gh_ctx}

Task: {task}

Respond with ONLY valid JSON:
{{
  "plan": "brief human-readable plan",
  "steps": [
    {{
      "tool": "git_ops",
      "args": {{"operation": "status", "repo_path": "."}},
      "description": "Check repo status"
    }}
  ]
}}
"""
    if ctx is None:
        return {
            "success": False,
            "error": "Context not available — sampling requires an active MCP session",
        }

    try:
        plan_response = await ctx.sample(
            messages=plan_prompt,
            max_tokens=1024,
        )
        plan_text = (plan_response.text if hasattr(plan_response, "text") else str(plan_response)) or ""
    except Exception as e:
        return {
            "success": False,
            "error": f"Planning failed: {e}",
            "hint": "Sampling requires MCP client support (e.g. Antigravity, Claude Desktop).",
        }

    import json

    try:
        clean = plan_text.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:])
            clean = clean.rsplit("```", 1)[0].strip()
        plan_data = json.loads(clean)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Could not parse plan JSON",
            "raw_plan": plan_text,
        }

    await ctx.info(f"Plan: {plan_data.get('plan', '?')} — {len(plan_data.get('steps', []))} steps")

    results = []
    for i, step in enumerate(plan_data.get("steps", [])):
        tool_name = step.get("tool")
        args = step.get("args", {})
        description = step.get("description", f"Step {i + 1}")

        await ctx.info(f"Step {i + 1}/{len(plan_data['steps'])}: {description}")

        try:
            if tool_name == "git_ops":
                args, refusal = await _gate_plan_step(tool_name, args)
                result = refusal if refusal is not None else await _git_ops(**args)
            elif tool_name == "github_ops":
                args, refusal = await _gate_plan_step(tool_name, args)
                result = refusal if refusal is not None else await asyncio.to_thread(_github_ops, **args)
            else:
                from .utils.response import error_response

                result = error_response(tool_name or "unknown", f"Unknown tool: {tool_name}")
        except Exception as e:
            from .utils.response import error_response

            result = error_response(tool_name or "unknown", str(e))

        results.append(
            {
                "step": i + 1,
                "description": description,
                "tool": tool_name,
                "args": args,
                "result": result,
                "success": result.get("success", False),
            }
        )

        if not result.get("success", False):
            await ctx.warning(f"Step {i + 1} failed: {result.get('error', 'unknown')}")
            break

    completed = sum(1 for r in results if r["success"])
    return {
        "success": completed == len(plan_data.get("steps", [])),
        "task": task,
        "plan": plan_data.get("plan"),
        "steps_total": len(plan_data.get("steps", [])),
        "steps_completed": completed,
        "results": results,
    }


@mcp.tool(annotations=_READ_ONLY)
async def git_github_search_workflow(
    task: str,
    owner: str | None = None,
    repo: str | None = None,
    limit: int = 30,
    ctx: Context | None = None,
) -> dict:
    """Agentic GitHub discovery/search workflow (sampling-first).

    Purpose:
    - Turn natural-language discovery tasks into multi-step github_ops calls.
    - Best for questions like:
      - "find repos with bak file dross"
      - "show me stale projects and archived repos"
      - "find repos tagged mcp with low maintenance activity"
    """
    if ctx is None:
        return {
            "success": False,
            "error": "Context not available — sampling requires an active MCP session",
        }

    await ctx.info(f"git_github_search_workflow: planning task: {task}")
    gh_ctx = f"owner={owner}, repo={repo}" if owner and repo else f"owner={owner}" if owner else "no owner/repo"

    plan_prompt = f"""You are a GitHub discovery planner.
Prefer the smallest chain of github_ops calls.

Available github_ops groups (all require valid gh auth unless read-only search fails first):
- Search & scan: search_repos, search_repos_topic (topic + optional owner/query),
  search_issues, search_code (set pretty=true for markdown + unique_repositories),
  code_find_repos (extension/path_pattern/owner scoped code hunt)
- Repos: repo_list, repo_view, show_repo (output_format markdown for human skim)
- Signals: issue_list, pr_list, release_list, workflow_list, workflow_runs
- Ecosystem: project_list/view, package_list/view
- LLM digest URLs (public repos / PAT for private): gitingest_link (owner, repo, ref?,
  subpath?), gitingest_convert_url (github_url= full tree URL), gitingest_help
- Sanity: auth_status when authentication might be the blocker
- Red shelf: repo_delete/release_delete need confirm=true in args plus working
  repo AI, else the step returns confirmation_required and stops the plan.

Context:
- {gh_ctx}
- limit={limit}

Task: {task}

Return ONLY valid JSON:
{{
  "plan": "short plan",
  "steps": [
    {{
      "tool": "github_ops",
      "args": {{"operation": "search_repos", "query": "topic:mcp", "limit": 20}},
      "description": "What this step does"
    }}
  ],
  "final_summary_strategy": "How to summarize findings for a human"
}}
"""
    try:
        plan_response = await ctx.sample(
            messages=plan_prompt,
            max_tokens=1200,
        )
        plan_text = (plan_response.text if hasattr(plan_response, "text") else str(plan_response)) or ""
    except Exception as e:
        return {
            "success": False,
            "error": f"Planning failed: {e}",
            "hint": "Sampling requires MCP client support (e.g. Antigravity, Claude Desktop).",
        }

    import json

    try:
        clean = plan_text.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:])
            clean = clean.rsplit("```", 1)[0].strip()
        plan_data = json.loads(clean)
    except json.JSONDecodeError:
        from .utils.response import error_response

        return error_response(
            "plan",
            "Could not parse plan JSON from LLM",
            recovery_options=["Try again with a more specific task"],
            suggested_fixes=["Shorten your task description"],
        )

    steps = plan_data.get("steps", [])
    await ctx.info(f"Discovery plan: {plan_data.get('plan', '?')} — {len(steps)} steps")

    results = []
    for i, step in enumerate(steps):
        args = step.get("args", {})
        desc = step.get("description", f"Step {i + 1}")
        await ctx.info(f"Step {i + 1}/{len(steps)}: {desc}")
        try:
            args, refusal = await _gate_plan_step("github_ops", args)
            result = refusal if refusal is not None else await asyncio.to_thread(_github_ops, **args)
        except Exception as e:
            from .utils.response import error_response

            result = error_response(args.get("operation", "unknown"), str(e))
        results.append(
            {
                "step": i + 1,
                "description": desc,
                "args": args,
                "result": result,
                "success": result.get("success", False),
            }
        )
        if not result.get("success", False):
            await ctx.warning(f"Step {i + 1} failed: {result.get('error', 'unknown')}")
            break

    completed = sum(1 for r in results if r["success"])
    return {
        "success": completed == len(steps),
        "task": task,
        "context": {"owner": owner, "repo": repo, "limit": limit},
        "plan": plan_data.get("plan"),
        "summary_strategy": plan_data.get("final_summary_strategy"),
        "steps_total": len(steps),
        "steps_completed": completed,
        "results": results,
    }


# ── Resources ─────────────────────────────────────────────────────────────────


@mcp.resource(
    "git://repo/status",
    description="Current git status of the default repo (cwd). Shows branch, changes, remote URL.",
)
async def resource_git_status() -> dict:
    """Live git status of the current working directory."""
    return await _git_ops(operation="status", repo_path=None)


@mcp.resource(
    "git://repo/log",
    description="Recent git commit log (last 20 commits) for the current repo.",
)
async def resource_git_log() -> dict:
    """Recent commit history of the current working directory."""
    return await _git_ops(operation="log", repo_path=None, max_count=20, oneline=True)


@mcp.resource(
    "git://{repo_path}/status",
    description="Git status for a specific repo path.",
)
async def resource_repo_status(repo_path: str) -> dict:
    """Live git status for a given repo path."""
    return await _git_ops(operation="status", repo_path=repo_path)


@mcp.resource(
    "git://{repo_path}/log",
    description="Recent commit log for a specific repo path.",
)
async def resource_repo_log(repo_path: str) -> dict:
    """Recent commits for a given repo path."""
    return await _git_ops(operation="log", repo_path=repo_path, max_count=20, oneline=True)


@mcp.resource(
    "github://{owner}/{repo}/issues",
    description="Open issues for a GitHub repository.",
)
def resource_github_issues(owner: str, repo: str) -> dict:
    """Open issues for owner/repo."""
    return _github_ops(operation="issue_list", owner=owner, repo=repo, state="open", limit=50)


@mcp.resource(
    "github://{owner}/{repo}/prs",
    description="Open pull requests for a GitHub repository.",
)
def resource_github_prs(owner: str, repo: str) -> dict:
    """Open PRs for owner/repo."""
    return _github_ops(operation="pr_list", owner=owner, repo=repo, state="open", limit=20)


@mcp.resource(
    "git://skills/concepts",
    description="Git/GitHub concept index for tutoring and quick lookup.",
)
def resource_git_skills_concepts() -> dict:
    """Concept index for the webapp/chat to ground explanations."""
    return {
        "concepts": [
            "rebase",
            "merge-vs-rebase",
            "cherry-pick",
            "revert-vs-reset",
            "stash",
            "worktree",
            "bisect",
            "interactive-rebase",
            "release-flow",
            "github-projects",
            "github-packages",
            "github-actions-debugging",
            "gitingest",
            "agentic-workflows",
        ],
        "hint": "Use git://skills/{topic} for a focused cheat-sheet.",
    }


@mcp.resource(
    "git://skills/{topic}",
    description="Focused Git/GitHub lecture notes for a topic (e.g., rebase).",
)
def resource_git_skill_topic(topic: str) -> dict:
    """Short, practical lecture note blocks keyed by topic."""
    t = topic.strip().lower()
    notes = {
        "rebase": {
            "what": "Reapply your commits onto a new base for a linear history.",
            "when": "Before opening/updating a PR; keeping feature branch current.",
            "commands": [
                "git fetch origin",
                "git rebase origin/main",
                "git rebase --continue | --abort",
            ],
            "danger": "Never rebase shared/published branch history unless team agrees.",
        },
        "merge-vs-rebase": {
            "what": "Merge preserves branch topology; rebase rewrites commit ancestry.",
            "when": "Merge for shared history clarity; rebase for cleaner PR branch history.",
            "commands": ["git merge main", "git rebase main"],
            "danger": "Rebase changes commit SHAs.",
        },
        "cherry-pick": {
            "what": "Copy specific commit(s) onto current branch.",
            "when": "Backporting fixes across release branches.",
            "commands": ["git cherry-pick <sha>", "git cherry-pick --abort"],
            "danger": "Can duplicate logical changes if also merged later.",
        },
        "gitingest": {
            "what": ("Turn a GitHub repo (or subpath) into one LLM-friendly text digest via gitingest.com."),
            "when": (
                "Quick full-repo or folder context without a local clone; check token size before pasting into prompts."
            ),
            "commands": [
                "github_ops(operation='gitingest_link', owner='ORG', repo='REPO')",
                "github_ops(operation='gitingest_convert_url', github_url='https://github.com/...')",
                "gitingest https://github.com/ORG/REPO --output -",
            ],
            "danger": (
                "Public by default; private repos need PAT. Complements llms.txt; does not replace llms-full.txt."
            ),
        },
        "agentic-workflows": {
            "what": ("Sampling tools that plan multi-step git_ops/github_ops chains from natural language."),
            "when": (
                "git_agentic_workflow: mixed local Git + GitHub tasks. "
                "git_github_search_workflow: discovery, search, repo intelligence only."
            ),
            "commands": [
                "git_agentic_workflow(task='…', repo_path?, owner?, repo?)",
                "git_github_search_workflow(task='…', owner?, repo?, limit?)",
            ],
            "danger": (
                "Prefer git_github_search_workflow / git_agentic_workflow in MCP hosts with "
                "full sampling (e.g. Antigravity) — LLM-planned steps are the superior path. "
                "POST /api/discovery presets are a portable fallback for web UI or hosts "
                "without sampling."
            ),
        },
    }
    if t not in notes:
        return {
            "topic": t,
            "found": False,
            "message": "Unknown topic. Start with git://skills/concepts",
        }
    return {"topic": t, "found": True, **notes[t]}


# ── Prompts ───────────────────────────────────────────────────────────────────


@mcp.prompt()
def git_commit_message(diff: str, context: str = "") -> str:
    """Generate a conventional commit message from a git diff.

    Args:
        diff: Output of git diff --staged
        context: Optional extra context (ticket number, feature description)
    """
    ctx_line = f"\nContext: {context}" if context else ""
    return (
        f"Write a conventional commit message for the following staged diff.{ctx_line}\n\n"
        "Rules:\n"
        "- Format: <type>(<scope>): <short description>\n"
        "- Types: feat, fix, docs, style, refactor, test, chore, ci, perf\n"
        "- Subject line max 72 chars, imperative mood\n"
        "- Add body if changes are non-trivial\n"
        "- Add BREAKING CHANGE footer if applicable\n"
        "- If the user has git-github-mcp: git_ops(operation='diff', repo_path=…) for unstaged\n\n"
        f"Diff:\n```\n{diff}\n```"
    )


@mcp.prompt()
def git_release_notes(
    commits: str,
    version: str,
    repo: str = "",
) -> str:
    """Generate release notes from a list of commits.

    Args:
        commits: Output of git log --oneline <prev_tag>..HEAD
        version: The new version tag (e.g. v1.2.0)
        repo: GitHub repo slug owner/repo (optional, for PR links)
    """
    repo_line = f"\nGitHub repo: {repo}" if repo else ""
    return (
        f"Write release notes for version {version}.{repo_line}\n\n"
        "Format:\n"
        "## What's Changed\n"
        "Group commits into: Features, Bug Fixes, Documentation, Internal.\n"
        "Skip trivial commits (chore: bump, style: format).\n"
        "Link PRs if GitHub repo provided.\n"
        "Optional: cross-check with github_ops release_list / pr_list for the repo.\n\n"
        f"Commits:\n```\n{commits}\n```"
    )


@mcp.prompt()
def git_pr_description(
    branch: str,
    commits: str,
    diff_stat: str = "",
) -> str:
    """Generate a pull request description.

    Args:
        branch: Feature branch name
        commits: Commit log for the branch
        diff_stat: Output of git diff --stat (optional)
    """
    stat_section = f"\nChanged files:\n```\n{diff_stat}\n```" if diff_stat else ""
    return (
        f"Write a pull request description for branch `{branch}`.\n\n"
        "Include:\n"
        "- ## Summary (what and why)\n"
        "- ## Changes (bullet list)\n"
        "- ## Testing (how to verify)\n"
        "- ## Notes (breaking changes, migration steps, TODOs)\n"
        f"{stat_section}\n\n"
        f"Commits:\n```\n{commits}\n```"
    )


@mcp.prompt()
def git_review_diff(diff: str, focus: str = "") -> str:
    """Code review prompt for a git diff.

    Args:
        diff: The diff to review (git diff or PR diff)
        focus: Optional focus area (security, performance, style, logic)
    """
    focus_line = f"\nFocus especially on: {focus}" if focus else ""
    return (
        f"Review the following code diff.{focus_line}\n\n"
        "For each issue found:\n"
        "- File and line reference\n"
        "- Severity: critical / major / minor / nit\n"
        "- Explanation and suggested fix\n\n"
        "Also note: what's done well.\n"
        "If the change touches GitHub config, mention whether Actions/workflows need updates.\n\n"
        f"Diff:\n```\n{diff}\n```"
    )


@mcp.prompt()
def github_issue_template(
    title: str,
    type: str = "bug",
    context: str = "",
) -> str:
    """Generate a well-structured GitHub issue body.

    Args:
        title: Issue title
        type: bug | feature | docs | question
        context: Any relevant context to include
    """
    templates = {
        "bug": (
            "Write a GitHub issue body for a bug report.\n"
            "Sections: Description, Steps to Reproduce, Expected Behavior, "
            "Actual Behavior, Environment, Additional Context."
        ),
        "feature": (
            "Write a GitHub issue body for a feature request.\n"
            "Sections: Problem Statement, Proposed Solution, Alternatives Considered, "
            "Implementation Notes."
        ),
        "docs": (
            "Write a GitHub issue body for a documentation improvement.\n"
            "Sections: Current Documentation, What's Missing or Wrong, Suggested Content."
        ),
        "question": (
            "Write a GitHub issue body for a question/discussion.\nSections: Question, What I've Tried, Relevant Code."
        ),
    }
    template = templates.get(type, templates["bug"])
    ctx_line = f"\nContext provided: {context}" if context else ""
    return f"{template}\n\nTitle: {title}{ctx_line}"


@mcp.prompt()
def github_debug_workflow(
    workflow_name: str,
    error_output: str,
    repo: str = "",
) -> str:
    """Debug a failing GitHub Actions workflow.

    Args:
        workflow_name: Name of the workflow file (e.g. ci.yml)
        error_output: The error output from the failing run
        repo: GitHub repo slug (optional)
    """
    repo_line = f"\nRepo: {repo}" if repo else ""
    return (
        f"Debug this failing GitHub Actions workflow: {workflow_name}{repo_line}\n\n"
        "Before guessing, prefer facts: workflow_runs, workflow_list, and recent commits "
        "if github_ops is available.\n\n"
        "Analyse the error, identify root cause, and provide:\n"
        "1. Root cause explanation\n"
        "2. Exact fix (YAML snippet or command)\n"
        "3. How to verify the fix\n\n"
        f"Error output:\n```\n{error_output}\n```"
    )


@mcp.prompt()
def git_github_explain_concept(concept: str, level: str = "intermediate") -> str:
    """Teaching prompt for Git/GitHub concepts with practical examples.

    Args:
        concept: e.g. rebase, cherry-pick, worktree, GitHub Projects, Packages, gitingest,
          agentic-workflows (git_agentic_workflow vs git_github_search_workflow)
        level: beginner | intermediate | advanced
    """
    return (
        f"Teach the concept '{concept}' at level '{level}'.\n\n"
        "Output structure:\n"
        "1. What it is (1-2 sentences)\n"
        "2. When to use it / when not to use it\n"
        "3. 2-4 practical commands/examples "
        "(include gh or git-github-mcp tool names when relevant)\n"
        "4. Common failure modes and recovery commands\n"
        "5. One short checklist the user can follow\n"
        "If the topic is Gitingest: contrast with committed llms.txt + llms-full.txt "
        "(curated vs live raw digest).\n"
        "Keep the explanation practical and non-fluffy."
    )


# ── FastAPI web bridge ────────────────────────────────────────────────────────

_mcp_http = mcp.http_app(path="/")

web_app = FastAPI(title=f"git-github-mcp Web Bridge v{VERSION}", lifespan=_mcp_http.lifespan)
web_app.include_router(_build_logs_router())

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:10714",
        "http://127.0.0.1:10714",
        "http://goliath:10714",
        "http://localhost:10713",
        "http://127.0.0.1:10713",
        "http://goliath:10713",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    ],
    allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@web_app.get("/health")
async def web_health():
    return {"ok": True, "service": "git-github-mcp", "version": VERSION, "port": WEB_PORT}


@web_app.get("/api/skills")
async def api_skills():
    return {
        "skills": [
            {
                "name": "github-expert",
                "title": "GitHub Expert",
                "description": (
                    "Expert Git and GitHub workflows -- use git_ops, github_ops, agentic workflows, Gitingest helpers."
                ),
            }
        ]
    }


@web_app.get("/api/skill/{skill_name}")
async def api_skill(skill_name: str):
    skill_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        ".cursor",
        "skills",
        "github-expert",
        "SKILL.md",
    )
    try:
        return {"content": Path(skill_path).read_text(encoding="utf-8")}
    except FileNotFoundError:
        return {
            "content": (
                "## Git GitHub MCP Expert\n\n"
                "You have 101+ operations across 11 tools. "
                "Use git_core/git_branch/git_admin/git_blame for local Git "
                "and github_ops for GitHub via gh CLI. "
                "Prefer agentic tools (git_agentic_workflow, "
                "git_github_search_workflow) for complex multi-step tasks."
            )
        }


# ── LLM / Chat ────────────────────────────────────────────────────────────────

_OLLAMA_BASE = "http://127.0.0.1:11434"
_LM_STUDIO_BASE = "http://127.0.0.1:1234"


def _probe_ollama_models() -> list[str]:
    import httpx

    try:
        r = httpx.get(f"{_OLLAMA_BASE}/api/tags", timeout=2.0)
        if r.status_code == 200:
            models = r.json().get("models", [])
            return [m["name"] for m in models]
    except Exception as exc:
        logger.debug("Ollama tags probe failed: %s", exc)
    return []


@web_app.get("/api/llm/discover")
async def api_llm_discover():
    import httpx

    providers = []
    ollama_available = False
    lm_studio_available = False
    ollama_models: list[str] = []

    try:
        r = httpx.get(f"{_OLLAMA_BASE}/api/tags", timeout=2.0)
        ollama_available = r.status_code == 200
        if ollama_available:
            ollama_models = [m["name"] for m in r.json().get("models", [])]
    except Exception as exc:
        logger.debug("Ollama discover probe failed: %s", exc)

    try:
        r = httpx.get(f"{_LM_STUDIO_BASE}/v1/models", timeout=2.0)
        lm_studio_available = r.status_code == 200
    except Exception as exc:
        logger.debug("LM Studio discover probe failed: %s", exc)

    if ollama_available:
        providers.append(
            {
                "id": "ollama",
                "name": "Ollama",
                "base_url": _OLLAMA_BASE,
                "models": ollama_models,
                "endpoint": "/api/chat",
            }
        )
    if lm_studio_available:
        providers.append(
            {
                "id": "lmstudio",
                "name": "LM Studio",
                "base_url": _LM_STUDIO_BASE,
                "models": [],
                "endpoint": "/v1/chat/completions",
            }
        )

    return {
        "success": True,
        "any_available": len(providers) > 0,
        "providers": providers,
        "ollama_models": ollama_models,
    }


@web_app.post("/api/chat")
async def api_chat(body: dict):
    import httpx

    messages = body.get("messages", [])
    model = body.get("model", "") or os.getenv("OLLAMA_MODEL", "gemma3:12b")
    provider = body.get("provider", "ollama")
    stream = body.get("stream", False)
    system_prompt = body.get("system_prompt", "")

    if provider == "lmstudio":
        base = _LM_STUDIO_BASE
        endpoint = "/v1/chat/completions"
    else:
        base = _OLLAMA_BASE
        endpoint = "/api/chat"

    if system_prompt:
        ollama_msgs = [{"role": "system", "content": system_prompt}, *messages]
    else:
        ollama_msgs = list(messages)

    payload = {"model": model, "messages": ollama_msgs, "stream": stream}
    if not stream:
        payload["options"] = {"temperature": 0.7}

    async def _generate():
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=5.0)) as client:
                async with client.stream("POST", f"{base}{endpoint}", json=payload, timeout=120.0) as resp:
                    if resp.status_code != 200:
                        yield json.dumps({"type": "error", "error": f"LLM returned {resp.status_code}"}) + "\n"
                        return
                    if not stream:
                        body_data = await resp.aread()
                        data = json.loads(body_data)
                        if provider == "ollama":
                            content = data.get("message", {}).get("content", "")
                        else:
                            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        yield json.dumps({"type": "token", "content": content}) + "\n"
                        yield json.dumps({"type": "done"}) + "\n"
                        return
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if provider == "ollama":
                            content = chunk.get("message", {}).get("content", "")
                            done = chunk.get("done", False)
                        else:
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            done = chunk.get("choices", [{}])[0].get("finish_reason") is not None
                        if content:
                            yield json.dumps({"type": "token", "content": content}) + "\n"
                        if done:
                            yield json.dumps({"type": "done"}) + "\n"
                            break
        except Exception as e:
            yield json.dumps({"type": "error", "error": str(e)}) + "\n"

    return StreamingResponse(_generate(), media_type="application/x-ndjson")


@web_app.get("/api/v1/health")
async def api_v1_health():
    return {
        "status": "ok",
        "server": "git-github-mcp",
        "version": VERSION,
        "uptime_seconds": round(time.time() - _START_TIME, 1),
        "tool_count": len(await mcp.list_tools()),
        "providers": {
            "git": "available",
            "github": "available",
        },
    }


@web_app.get("/api/v1/diagnostics")
async def api_v1_diagnostics():
    import platform as _platform

    tools_list = await mcp.list_tools()
    tool_names = [t.name for t in tools_list if not t.name.startswith("_")]
    return {
        "status": "ok",
        "server": "git-github-mcp",
        "version": VERSION,
        "uptime_seconds": round(time.time() - _START_TIME, 1),
        "tool_count": len(tool_names),
        "tools": [{"name": n} for n in tool_names],
        "system": {"windows": _platform.system() == "Windows", "python": _platform.python_version()},
        "errors": [],
    }


@web_app.get("/api/capabilities")
async def api_capabilities():
    return await build_capabilities(mcp, version=VERSION)


@web_app.get("/api/apps")
async def api_apps():
    """Fleet apps hub — entries with webapp ports from fleet registry (enriched)."""
    from .services.fleet_catalog import load_registry

    def _read_pyproject_desc(repo_path: Path) -> str | None:
        p = repo_path / "pyproject.toml"
        if not p.is_file():
            return None
        try:
            import tomllib

            data = tomllib.loads(p.read_text(encoding="utf-8"))
            desc = str(data.get("project", {}).get("description") or "").strip()
            if desc and len(desc) >= 10 and "hardened substrate" not in desc.lower():
                return desc
        except Exception:
            pass
        # fallback regex for older Python without tomllib or bad toml
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
            import re

            m = re.search(r'description\s*=\s*["\']([^"\']+)["\']', txt)
            if m:
                d = m.group(1).strip()
                if len(d) >= 10 and "hardened substrate" not in d.lower():
                    return d
        except Exception:
            pass
        return None

    def _last_commit(repo_path: Path) -> str | None:
        # fast git log, no gh call
        from .services.fleet_common import run_git

        ok, out, _ = run_git(["log", "-1", "--format=%ci", "--no-merges"], repo_path)
        if ok and out.strip():
            return out.strip()
        return None

    def _has_tauri(repo_path: Path) -> bool:
        return (repo_path / "native" / "tauri.conf.json").is_file() or (
            repo_path / "src-tauri" / "tauri.conf.json"
        ).is_file()

    def _is_hype(desc: str) -> bool:
        low = desc.lower()
        return (
            any(k in low for k in ["industrial-grade", "agentic revolution", "hardened substrate"])
            or len(desc.strip()) < 12
        )

    rows = load_registry()
    apps: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rid = str(row.get("id") or "")
        port = int(row.get("frontend_port") or row.get("port") or 0)
        if port <= 0:
            continue
        raw_desc = str(row.get("description") or "")
        cat = str(row.get("category") or "mcp")
        # enrich description: prefer pyproject if registry is hype/missing
        desc = raw_desc
        repo_path = Path(str(row.get("repo_path") or f"D:/Dev/repos/{rid}"))
        if _is_hype(raw_desc) or not raw_desc.strip():
            py_desc = None
            # file read is fast, sync is fine
            py_desc = _read_pyproject_desc(repo_path)
            if py_desc:
                desc = py_desc
            elif cat and cat.lower() != "mcp":
                desc = cat
            else:
                desc = raw_desc or "Fleet MCP — local webapp"
        has_tauri = _has_tauri(repo_path)
        # installed Tauri exe check (current user)
        has_tauri_installed = False
        if has_tauri:
            for cand in [
                Path.home() / "AppData" / "Local" / "Programs" / rid / f"{rid}.exe",
                repo_path / "native" / "target" / "release" / f"{rid}.exe",
            ]:
                if cand.is_file():
                    has_tauri_installed = True
                    break
        gh_owner = str(row.get("github_owner") or "sandraschi")
        gh_repo = str(row.get("github_repo") or rid)
        gh_url = f"https://github.com/{gh_owner}/{gh_repo}"
        # last commit is expensive (200 git calls) - return None here, frontend sorts by name/port; use /api/apps/health for recent if needed
        last_commit = None
        # optional: uncomment to enable recent sort (adds ~6s): last_commit = _last_commit(repo_path) if repo_path.is_dir() else None
        apps.append(
            {
                "id": rid,
                "name": str(row.get("name") or rid),
                "description": desc,
                "raw_description": raw_desc,
                "pyproject_description": _read_pyproject_desc(repo_path),
                "port": port,
                "backend_port": int(row.get("port") or 0),
                "category": cat,
                "url": f"http://127.0.0.1:{port}",
                "gh_url": gh_url,
                "repo_path": str(repo_path),
                "has_tauri": has_tauri,
                "has_tauri_installed": has_tauri_installed,
                "last_commit": last_commit,
            }
        )
    apps.sort(key=lambda a: a["port"])
    log_activity("api", f"apps hub listed {len(apps)} entries (enriched)", level="INFO")
    return {"apps": apps, "fleet_total": len(rows)}


def _check_port_health_sync(port: int, timeout: float = 1.2) -> dict:
    import socket

    # quick TCP connect
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            pass
    except Exception as e:
        return {
            "port": port,
            "alive": False,
            "reason": f"tcp refused: {e}",
            "health_url": f"http://127.0.0.1:{port}/health",
        }

    # try health endpoints (include depot /api/capabilities and robotics /api/v1/health)
    for path in (
        "/health",
        "/api/health",
        "/api/status",
        "/api/capabilities",
        "/api/v1/health",
        "/api/capabilities/health",
    ):
        try:
            import httpx

            with httpx.Client(timeout=timeout) as c:
                r = c.get(f"http://127.0.0.1:{port}{path}")
                if 200 <= r.status_code < 500:
                    # 200-499 means something is listening
                    return {
                        "port": port,
                        "alive": True,
                        "status_code": r.status_code,
                        "health_url": f"http://127.0.0.1:{port}{path}",
                        "reason": "http ok",
                    }
        except Exception:
            continue
    return {
        "port": port,
        "alive": True,
        "reason": "tcp open but health 404",
        "health_url": f"http://127.0.0.1:{port}/health",
    }


@web_app.get("/api/apps/health")
async def api_apps_health(port: int):
    result = await asyncio.to_thread(_check_port_health_sync, port)
    return result


def _is_process_running(name: str) -> list[int]:
    import subprocess

    try:
        out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {name}.exe"], capture_output=True, text=True, timeout=4)
        pids: list[int] = []
        for line in out.stdout.splitlines():
            if name.lower() in line.lower() and ".exe" in line.lower():
                parts = line.split()
                for p in parts:
                    if p.isdigit():
                        try:
                            pid = int(p)
                            if pid > 4:
                                pids.append(pid)
                        except Exception:
                            pass
        return pids
    except Exception:
        return []


def _bring_to_foreground(pids: list[int]) -> bool:
    import subprocess

    if not pids:
        return False
    # Use powershell User32 SetForegroundWindow for first pid's main window
    pid = pids[0]
    ps = f"""
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class Win {{ [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd); [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow); }}
'@
$p = Get-Process -Id {pid} -ErrorAction SilentlyContinue
if ($p) {{
  $h = $p.MainWindowHandle
  if ($h -eq 0) {{ $h = $p.Handle }}
  [Win]::ShowWindow($h, 9) | Out-Null
  [Win]::SetForegroundWindow($h) | Out-Null
  exit 0
}}
exit 1
"""
    try:
        r = subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps], timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def _find_starts_for_id(app_id: str) -> list[str]:
    candidates: list[str] = []

    def _try_ids(base_id: str) -> list[str]:
        ids_to_try = [base_id]
        if base_id.endswith("-mcp"):
            ids_to_try.append(base_id[:-4])
            ids_to_try.append(base_id[:-4].replace("-mcp", ""))
        # also try without suffix for cases like virtualization-mcp -> virtualization
        return ids_to_try

    for cand_id in _try_ids(app_id):
        mcd = Path(r"D:\Dev\repos\mcp-central-docs\starts") / f"{cand_id}-start.bat"
        if mcd.exists() and str(mcd) not in candidates:
            candidates.append(str(mcd))
    for cand_id in _try_ids(app_id):
        repo_ps1 = Path(r"D:\Dev\repos") / cand_id / "start.ps1"
        if repo_ps1.exists() and str(repo_ps1) not in candidates:
            candidates.append(str(repo_ps1))
        repo_bat = Path(r"D:\Dev\repos") / cand_id / "start.bat"
        if repo_bat.exists() and str(repo_bat) not in candidates:
            candidates.append(str(repo_bat))
    # 4. Tauri installed exe (current user)
    tauri_candidates = [
        Path.home() / "AppData" / "Local" / "Programs" / app_id / f"{app_id}.exe",
        Path.home() / "AppData" / "Local" / app_id / f"{app_id}.exe",
        Path(r"D:\Dev\repos") / app_id / "native" / "target" / "release" / f"{app_id}.exe",
        Path(r"D:\Dev\repos")
        / app_id
        / "native"
        / "target"
        / "release"
        / "bundle"
        / "nsis"
        / f"{app_id}_0.5.0_x64-setup.exe",
    ]
    for p in tauri_candidates:
        if p.exists():
            candidates.append(str(p))
    return candidates


@web_app.post("/api/apps/ensure")
async def api_apps_ensure(payload: dict):
    app_id = str(payload.get("id") or payload.get("app_id") or "").strip()
    port = int(payload.get("port") or 0)
    if not app_id and port:
        # try to resolve id from registry by port
        from .services.fleet_catalog import load_registry

        for row in load_registry():
            if int(row.get("frontend_port") or row.get("port") or 0) == port:
                app_id = str(row.get("id") or "")
                break
    if not port and app_id:
        from .services.fleet_catalog import load_registry

        for row in load_registry():
            if str(row.get("id")) == app_id:
                port = int(row.get("frontend_port") or row.get("port") or 0)
                break
    if not port:
        return {"success": False, "error": "port or id required", "alive": False}

    # 1. already healthy? also check backend_port for dual-port apps (depot-mcp 10726/10727)
    health = await asyncio.to_thread(_check_port_health_sync, port)
    # fallback: check backend_port from registry if frontend not alive
    if not health.get("alive") and app_id:
        try:
            from .services.fleet_catalog import load_registry

            for row in load_registry():
                if str(row.get("id")) == app_id:
                    bport = int(row.get("port") or 0)
                    fport = int(row.get("frontend_port") or 0)
                    cand = bport if bport != port and bport > 0 else (fport if fport != port and fport > 0 else 0)
                    if cand:
                        h2 = await asyncio.to_thread(_check_port_health_sync, cand)
                        if h2.get("alive"):
                            health = h2
                            port = cand
                    break
        except Exception:
            pass
    if health.get("alive"):
        # also try to bring existing window to front if Tauri
        if app_id:
            pids = await asyncio.to_thread(_is_process_running, app_id)
            if pids:
                await asyncio.to_thread(_bring_to_foreground, pids)
                return {
                    "success": True,
                    "status": "brought_to_foreground",
                    "alive": True,
                    "url": f"http://127.0.0.1:{port}",
                    "pids": pids,
                    "port": port,
                    "id": app_id,
                }
        return {
            "success": True,
            "status": "already_running",
            "alive": True,
            "url": f"http://127.0.0.1:{port}",
            "port": port,
            "id": app_id,
        }

    # 2. Tauri winapp already running but port not healthy? bring to front
    if app_id:
        pids = await asyncio.to_thread(_is_process_running, app_id)
        # also check -native suffix
        if not pids:
            pids = await asyncio.to_thread(_is_process_running, f"{app_id}-native")
        if pids:
            ok = await asyncio.to_thread(_bring_to_foreground, pids)
            # re-check health after bringing to front (maybe it was minimized)
            health2 = await asyncio.to_thread(_check_port_health_sync, port)
            return {
                "success": True,
                "status": "brought_to_foreground" if ok else "found_process",
                "alive": bool(health2.get("alive")),
                "url": f"http://127.0.0.1:{port}",
                "pids": pids,
                "port": port,
                "id": app_id,
            }

    # 3. try to start via starts
    if app_id:
        candidates = await asyncio.to_thread(_find_starts_for_id, app_id)
        # prefer mcd start.bat, then start.ps1
        start_cmd = None
        for c in candidates:
            if c.lower().endswith("-start.bat") or c.lower().endswith("start.ps1"):
                start_cmd = c
                break
        if start_cmd:
            try:
                import subprocess

                # launch detached
                if start_cmd.lower().endswith(".ps1"):
                    subprocess.Popen(
                        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", start_cmd],
                        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
                    )
                else:
                    subprocess.Popen(
                        ["cmd.exe", "/c", start_cmd],
                        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
                    )
                # poll health up to 12s
                for _ in range(12):
                    await asyncio.sleep(1)
                    h = await asyncio.to_thread(_check_port_health_sync, port)
                    if h.get("alive"):
                        return {
                            "success": True,
                            "status": "started",
                            "alive": True,
                            "url": f"http://127.0.0.1:{port}",
                            "port": port,
                            "id": app_id,
                            "via": start_cmd,
                        }
                return {
                    "success": True,
                    "status": "start_initiated",
                    "alive": False,
                    "url": f"http://127.0.0.1:{port}",
                    "port": port,
                    "id": app_id,
                    "via": start_cmd,
                    "note": "started but health not yet ok - wait a few seconds and retry",
                }
            except Exception as e:
                return {"success": False, "error": str(e), "port": port, "id": app_id}

        # fallback: try Tauri exe directly
        for c in candidates:
            if c.lower().endswith(".exe") and "setup" not in c.lower():
                try:
                    import subprocess

                    subprocess.Popen([c], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0)
                    return {
                        "success": True,
                        "status": "tauri_started",
                        "alive": False,
                        "url": f"http://127.0.0.1:{port}",
                        "port": port,
                        "id": app_id,
                        "via": c,
                    }
                except Exception as e:
                    return {"success": False, "error": str(e), "port": port, "id": app_id}
        return {
            "success": False,
            "error": f"no start entry found for {app_id} (checked {candidates})",
            "port": port,
            "id": app_id,
        }

    return {"success": False, "error": "could not start - no id", "port": port}


@web_app.get("/api/status")
async def api_status():
    result = await asyncio.to_thread(_get_status, level="basic")
    if isinstance(result, dict):
        result["version"] = VERSION
        result["git_ops"] = len(CORE_OPS) + len(BRANCH_OPS) + len(ADMIN_OPS)
        from .tools.github_ops import ACTION_TYPE

        result["github_ops"] = len(ACTION_TYPE)
    return result


# Mount MCP HTTP transport alongside the web API
web_app.mount("/mcp", _mcp_http)


@web_app.get("/api/tools")
async def api_tools():
    return {
        "tools": [
            {"name": "git_core", "operations": 11, "description": "status/log/diff/add/commit/push/pull/fetch"},
            {"name": "git_branch", "operations": 14, "description": "branch lifecycle, merge, rebase, stash, tag"},
            {"name": "git_admin", "operations": 16, "description": "remote/reset/revert/clean/submodule/bisect"},
            {"name": "git_blame", "operations": 1, "description": "annotate file lines with commit info"},
            {"name": "github_ops", "operations": 58, "description": "GitHub API via gh CLI"},
            {
                "name": "git_agentic_workflow",
                "description": "Agentic multi-step Git/GitHub operations",
            },
            {
                "name": "git_github_search_workflow",
                "description": "Agentic multi-step GitHub discovery/search workflow",
            },
            {
                "name": "web_discovery",
                "description": (
                    f"HTTP POST /api/discovery — {len(DISCOVERY_PRESETS)} preset chains "
                    "(fallback when MCP sampling unavailable; prefer git_github_search_workflow "
                    "in full-sampling clients e.g. Antigravity)"
                ),
                "presets": list(DISCOVERY_PRESETS),
            },
            {
                "name": "fleet_morning_digest",
                "description": "Daily fleet PR/issue/notification breakfast summary",
            },
            {
                "name": "fleet_ops",
                "description": "Fleet maintainer toolkit (16 ops incl. full_suite)",
                "operations": [
                    "registry_load",
                    "port_audit",
                    "docs_gate",
                    "quarantine_report",
                    "ci_pulse",
                    "dependabot_digest",
                    "mention_inbox",
                    "ack_drafts",
                    "local_dirty",
                    "release_drift",
                    "grade_snapshot",
                    "gitingest_bundle",
                    "runner_status",
                    "weekly_retro",
                    "council_payload",
                    "full_suite",
                ],
            },
            {"name": "git_github_status", "description": "System status"},
            {"name": "git_github_help", "description": "Contextual help"},
        ]
    }


@web_app.post("/api/git")
async def api_git(body: dict):
    args = body.get("arguments", body)
    op = args.get("operation", "?")
    log_activity("git_ops", f"operation={op}", level="INFO", meta={"operation": op})
    return await _git_ops(**args)


@web_app.post("/api/github")
async def api_github(body: dict):
    args = body.get("arguments", body)
    op = args.get("operation", "?")
    log_activity("github_ops", f"operation={op}", level="INFO", meta={"operation": op})
    # REST calls the implementation directly — the red-shelf gate lives in the
    # MCP wrapper above. Humans in the webapp confirm by clicking.
    return await asyncio.to_thread(_github_ops, **args)


@web_app.post("/api/morning-digest")
async def api_morning_digest(body: dict | None = None):
    """Run fleet morning digest (same as fleet_morning_digest MCP tool)."""
    args = body or {}
    return await asyncio.to_thread(_run_morning_digest, **args)


@web_app.post("/api/fleet-ops")
async def api_fleet_ops(body: dict | None = None):
    """Run a single fleet_ops operation (same as fleet_ops MCP tool)."""
    args = body or {}
    operation = args.pop("operation", "")
    return await asyncio.to_thread(_fleet_ops, operation, **args)


@web_app.post("/api/fleet-suite")
async def api_fleet_suite(body: dict | None = None):
    """Run full fleet maintainer suite (fleet_ops operation=full_suite)."""
    args = body or {}

    def _run_and_cache() -> dict:
        result = _fleet_ops("full_suite", **args)
        if isinstance(result, dict):
            _cache_suite_result(result)
        return result

    return await asyncio.to_thread(_run_and_cache)


_suite_last: dict | None = None
_suite_last_lock = threading.Lock()


def _cache_suite_result(result: dict) -> None:
    global _suite_last
    with _suite_last_lock:
        _suite_last = result


@web_app.get("/api/fleet-suite/last")
async def api_fleet_suite_last():
    """Latest full_suite result (populated by /api/fleet-suite/stream)."""
    with _suite_last_lock:
        if _suite_last is None:
            return {"success": False, "error": "No fleet suite result cached yet"}
        return _suite_last


def _fleet_suite_stream_args(body: dict | None) -> dict:
    args = body or {}
    return {
        "fleet_repos": args.get("fleet_repos"),
        "fleet_repos_file": args.get("fleet_repos_file"),
        "use_registry": bool(args.get("use_registry", True)),
        "stale_days": int(args.get("stale_days", 7) or 7),
        "deliver": args.get("deliver"),
        "maintainer_login": args.get("maintainer_login"),
        "since_last_run": bool(args.get("since_last_run", True)),
    }


@web_app.post("/api/fleet-suite/stream")
async def api_fleet_suite_stream(body: dict | None = None):
    """Stream NDJSON progress events while running full_suite; final line is done or error."""
    stream_args = _fleet_suite_stream_args(body)
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=512)

    def progress(event: dict) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, {"type": "progress", **event})

    def worker() -> None:
        try:
            result = _run_full_suite(**stream_args, on_progress=progress)
            _cache_suite_result(result)
            # Lightweight done — full payload is huge; client fetches /api/fleet-suite/last
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {
                    "type": "done",
                    "success": bool(result.get("success")),
                    "message": result.get("message"),
                },
            )
        except Exception as exc:
            loop.call_soon_threadsafe(queue.put_nowait, {"type": "error", "error": str(exc)})

    async def generate():
        threading.Thread(target=worker, daemon=True).start()
        while True:
            item = await queue.get()
            yield json.dumps(item, default=str) + "\n"
            if item.get("type") in ("done", "error"):
                break

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@web_app.post("/api/discovery")
async def api_discovery(body: dict):
    """Preset GitHub discovery for the HTTP bridge.

    Prefer MCP git_github_search_workflow when the client supports full sampling
    (e.g. Antigravity): LLM-planned steps are the superior path. This route is for
    the web UI and for MCP hosts without sampling.
    """
    args = body.get("arguments", body)
    preset = args.get("preset", "")
    raw_lim = args.get("limit", 25)
    try:
        lim = int(raw_lim)
    except (TypeError, ValueError):
        lim = 25
    return await asyncio.to_thread(
        _run_discovery_workflow,
        preset,
        owner=args.get("owner"),
        repo=args.get("repo"),
        query=args.get("query"),
        topic=args.get("topic"),
        extension=args.get("extension"),
        limit=lim,
    )


# Serve React webapp from web/dist if built
_dist = os.path.join(os.path.dirname(__file__), "..", "..", "..", "web", "dist")
if os.path.isdir(_dist):
    web_app.mount("/", StaticFiles(directory=_dist, html=True), name="static")


def main():
    from .transport import get_transport_config, run_server

    cfg = get_transport_config()
    transport = cfg.get("transport", "stdio")

    if transport != "http" and os.getenv("GIT_GITHUB_WEB", "0") == "1":
        # Opt-in only. web_app carries the FastMCP lifespan from mcp.http_app(),
        # so running it alongside stdio can double-start the session manager.
        # daemon=True so the process dies when the client closes stdin, which
        # also prevents the orphan holding WEB_PORT across restarts (WinError 10048).
        threading.Thread(
            target=lambda: uvicorn.run(web_app, host=WEB_HOST, port=WEB_PORT, log_level="warning"),
            daemon=True,
        ).start()
        logger.info(f"HTTP bridge running on {WEB_HOST}:{WEB_PORT}")

    # stdio: run_stdio_async owns the main thread (required for Claude Desktop).
    # http:  the transport module serves MCP over streamable HTTP itself.
    try:
        run_server(mcp, server_name="git-github-mcp")
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")

    logger.info("git-github-mcp stopped")


if __name__ == "__main__":
    main()
