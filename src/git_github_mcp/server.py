"""git-github-mcp server — FastMCP 3.1+, portmanteau pattern.

Tools:     git_ops (43), github_ops (58), git_github_status, git_github_help,
           git_agentic_workflow, git_github_search_workflow (sampling / agentic)
Resources: git://repo/*, github://owner/repo/*, git://skills/*
Prompts:   git_commit_message, git_release_notes, git_pr_description,
           git_review_diff, github_issue_template, github_debug_workflow,
           git_github_explain_concept
Web:       FastAPI bridge (e.g. POST /api/git, /api/github, /api/discovery)
"""

import logging
import os
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastmcp import Context, FastMCP

from .tools.git_ops import git_ops as _git_ops
from .tools.github_ops import github_ops as _github_ops
from .tools.help import get_help as _get_help
from .tools.status import get_status as _get_status
from .web_discovery import PRESETS as DISCOVERY_PRESETS
from .web_discovery import run_discovery_workflow as _run_discovery_workflow

logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")
logger = logging.getLogger("git-github-mcp")

VERSION = "0.4.0"
WEB_PORT = int(os.getenv("WEB_PORT", "10702"))
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")


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
        "Use git_ops for local repository work (43 actions). "
        "Use github_ops for GitHub API operations via gh CLI (58 actions). "
        "Use git_github_help for full operation reference. "
        "Use git_agentic_workflow for multi-step operations that require reasoning. "
        "Use git_github_search_workflow for agentic GitHub discovery/search tasks."
    ),
)


# ── Tools ─────────────────────────────────────────────────────────────────────


@mcp.tool()
async def git_ops(
    operation: str,
    repo_path: str | None = None,
    # add / commit
    message: str | None = None,
    files: list[str] | None = None,
    all_files: bool = False,
    amend: bool = False,
    # push / pull / fetch
    remote: str = "origin",
    branch: str | None = None,
    force: bool = False,
    set_upstream: bool = False,
    # clone / init
    repo_url: str | None = None,
    target_dir: str | None = None,
    initial_branch: str = "main",
    # log / diff / show / blame
    max_count: int = 20,
    commit: str | None = None,
    commit2: str | None = None,
    oneline: bool = False,
    file_path: str | None = None,
    # branch
    source_branch: str | None = None,
    # stash
    stash_message: str | None = None,
    stash_index: int = 0,
    # tag
    tag_name: str | None = None,
    tag_message: str | None = None,
    # reset
    mode: str = "mixed",
    # remote
    remote_url: str | None = None,
    remote_name: str | None = None,
    # clean
    dry_run: bool = False,
    include_dirs: bool = False,
    # submodule
    submodule_url: str | None = None,
    submodule_path: str | None = None,
    recursive: bool = False,
    # worktree
    worktree_path: str | None = None,
) -> dict:
    """Local Git operations — 43 actions.

    CORE:      init, clone, add, commit, push, pull, fetch, status
    INSPECT:   log, diff, show, blame
    BRANCH:    branch_list, branch_create, branch_switch, branch_delete, branch_merge, rebase
    REMOTE:    remote_list, remote_add, remote_remove
    STASH:     stash, stash_pop, stash_list, stash_drop
    TAG:       tag_list, tag_create, tag_delete
    UNDO:      reset, revert, cherry_pick
    CLEANUP:   clean
    SUBMODULE: submodule_add, submodule_update, submodule_sync, submodule_status
    BISECT:    bisect_start, bisect_bad, bisect_good, bisect_reset
    WORKTREE:  worktree_add, worktree_list, worktree_remove
    """
    start = time.perf_counter()
    result = _git_ops(
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
    )
    result["execution_time_ms"] = round((time.perf_counter() - start) * 1000, 2)
    return result


@mcp.tool()
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
) -> dict:
    """GitHub operations via gh CLI — 58 actions. Requires: gh auth login.

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
    """
    start = time.perf_counter()
    result = _github_ops(
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


@mcp.tool()
async def git_github_status(level: str = "basic") -> dict:
    """System status: git and gh CLI availability, versions, auth state."""
    return _get_status(level=level)


@mcp.tool()
async def git_github_help(level: str = "basic", topic: str | None = None) -> dict:
    """Contextual help for git-github-mcp tools and operations.

    level: basic | intermediate | advanced
    topic: git_ops | github_ops | None (all)
    """
    return _get_help(level=level, topic=topic)


@mcp.tool()
async def git_agentic_workflow(
    task: str,
    repo_path: str | None = None,
    owner: str | None = None,
    repo: str | None = None,
    ctx: Context = None,
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

    # Build context string for the planner
    repo_ctx = f"repo_path={repo_path}" if repo_path else "repo_path=. (cwd)"
    gh_ctx = f"owner={owner}, repo={repo}" if owner and repo else "no GitHub repo specified"

    plan_prompt = f"""You are a Git/GitHub operations planner. Given a task, output a JSON plan.

Available tools:
- git_ops(operation, repo_path, ...): 43 local git actions (init, clone, status, add,
  commit, push, pull, fetch, log, diff, show, blame, branch lifecycle, rebase, remote,
  stash, tag, reset, revert, cherry_pick, submodule_*, bisect_*, worktree_*, clean).
- github_ops(operation, owner, repo, ...): 58 GitHub actions via gh CLI:
  repos (repo_list, repo_view, show_repo, create/fork/clone/delete/rename/archive),
  issues (list/view/create/close/comment), PRs (list/view/create/merge/checkout/close/comment),
  releases (full CRUD), Actions workflows (list/run/runs/cancel/enable/disable),
  labels, secrets, collaborators,
  search (search_repos, search_repos_topic, search_issues, search_code with pretty=,
  code_find_repos for extension/path-scoped hunts),
  Projects (project_*), Packages (package_*),
  Gitingest helpers (gitingest_link, gitingest_convert_url with github_url, gitingest_help;
  optional ref, subpath on link),
  auth_status, gist_list.

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

    try:
        plan_response = await ctx.sample(
            messages=[{"role": "user", "content": plan_prompt}],
            max_tokens=1024,
        )
        plan_text = plan_response.text if hasattr(plan_response, "text") else str(plan_response)
    except Exception as e:
        return {
            "success": False,
            "error": f"Planning failed: {e}",
            "hint": "Sampling requires MCP client support (e.g. Antigravity, Claude Desktop).",
        }

    # Parse the plan
    import json

    try:
        # Strip markdown fences if present
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

    # Execute steps
    results = []
    for i, step in enumerate(plan_data.get("steps", [])):
        tool_name = step.get("tool")
        args = step.get("args", {})
        description = step.get("description", f"Step {i + 1}")

        await ctx.info(f"Step {i + 1}/{len(plan_data['steps'])}: {description}")

        try:
            if tool_name == "git_ops":
                result = _git_ops(**args)
            elif tool_name == "github_ops":
                result = _github_ops(**args)
            else:
                result = {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            result = {"success": False, "error": str(e)}

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

        # Stop on hard failure
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


@mcp.tool()
async def git_github_search_workflow(
    task: str,
    owner: str | None = None,
    repo: str | None = None,
    limit: int = 30,
    ctx: Context = None,
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
    gh_ctx = (
        f"owner={owner}, repo={repo}"
        if owner and repo
        else f"owner={owner}"
        if owner
        else "no owner/repo"
    )

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
            messages=[{"role": "user", "content": plan_prompt}],
            max_tokens=1200,
        )
        plan_text = plan_response.text if hasattr(plan_response, "text") else str(plan_response)
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
        return {"success": False, "error": "Could not parse plan JSON", "raw_plan": plan_text}

    steps = plan_data.get("steps", [])
    await ctx.info(f"Discovery plan: {plan_data.get('plan', '?')} — {len(steps)} steps")

    results = []
    for i, step in enumerate(steps):
        args = step.get("args", {})
        desc = step.get("description", f"Step {i + 1}")
        await ctx.info(f"Step {i + 1}/{len(steps)}: {desc}")
        if args.get("operation") == "auth_status":
            # Allow explicit auth checks but keep this workflow discovery-focused.
            pass
        try:
            result = _github_ops(**args)
        except Exception as e:
            result = {"success": False, "error": str(e)}
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
def resource_git_status() -> dict:
    """Live git status of the current working directory."""
    return _git_ops(operation="status", repo_path=None)


@mcp.resource(
    "git://repo/log",
    description="Recent git commit log (last 20 commits) for the current repo.",
)
def resource_git_log() -> dict:
    """Recent commit history of the current working directory."""
    return _git_ops(operation="log", repo_path=None, max_count=20, oneline=True)


@mcp.resource(
    "git://{repo_path}/status",
    description="Git status for a specific repo path.",
)
def resource_repo_status(repo_path: str) -> dict:
    """Live git status for a given repo path."""
    return _git_ops(operation="status", repo_path=repo_path)


@mcp.resource(
    "git://{repo_path}/log",
    description="Recent commit log for a specific repo path.",
)
def resource_repo_log(repo_path: str) -> dict:
    """Recent commits for a given repo path."""
    return _git_ops(operation="log", repo_path=repo_path, max_count=20, oneline=True)


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
            "what": (
                "Turn a GitHub repo (or subpath) into one LLM-friendly text digest "
                "via gitingest.com."
            ),
            "when": (
                "Quick full-repo or folder context without a local clone; "
                "check token size before pasting into prompts."
            ),
            "commands": [
                "github_ops(operation='gitingest_link', owner='ORG', repo='REPO')",
                "github_ops(operation='gitingest_convert_url', github_url='https://github.com/...')",
                "gitingest https://github.com/ORG/REPO --output -",
            ],
            "danger": (
                "Public by default; private repos need PAT. Complements llms.txt; "
                "does not replace llms-full.txt."
            ),
        },
        "agentic-workflows": {
            "what": (
                "Sampling tools that plan multi-step git_ops/github_ops chains "
                "from natural language."
            ),
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
            "Write a GitHub issue body for a question/discussion.\n"
            "Sections: Question, What I've Tried, Relevant Code."
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

web_app = FastAPI(title=f"git-github-mcp Web Bridge v{VERSION}")

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@web_app.get("/api/status")
async def api_status():
    return _get_status(level="basic")


@web_app.get("/api/tools")
async def api_tools():
    return {
        "tools": [
            {"name": "git_ops", "operations": 43, "description": "Local Git repository operations"},
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
            {"name": "git_github_status", "description": "System status"},
            {"name": "git_github_help", "description": "Contextual help"},
        ]
    }


@web_app.post("/api/git")
async def api_git(body: dict):
    args = body.get("arguments", body)
    return await git_ops(**args)


@web_app.post("/api/github")
async def api_github(body: dict):
    args = body.get("arguments", body)
    return await github_ops(**args)


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
    return _run_discovery_workflow(
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
    from .transport import run_server

    if os.getenv("MCP_TRANSPORT") == "http" or "--http" in __import__("sys").argv:
        logger.info(f"Starting web bridge on {WEB_HOST}:{WEB_PORT}")
        uvicorn.run(web_app, host=WEB_HOST, port=WEB_PORT)
    else:
        run_server(mcp, server_name="git-github-mcp")
