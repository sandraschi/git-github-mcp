"""Multi-step GitHub discovery presets for the HTTP web bridge.

Portable fallback: fixed github_ops chains without the host's LLM planner.

**Preferred path** when the MCP client supports sampling: use tool
``git_github_search_workflow`` (and ``git_agentic_workflow`` for mixed Git+GitHub tasks)
— e.g. Antigravity and other full-sampling hosts get LLM-planned, adaptive steps.
This module serves the web UI and any environment where sampling is unavailable.
"""

from __future__ import annotations

from typing import Any

from .tools.github_ops import github_ops as _github_ops

PRESETS: tuple[str, ...] = (
    "org_snapshot",
    "topic_hunt",
    "code_sweep",
    "repo_deep_dive",
    "global_search",
)


def _call(op: str, **kw: Any) -> dict[str, Any]:
    args = {k: v for k, v in kw.items() if v is not None}
    return _github_ops(operation=op, **args)


def run_discovery_workflow(
    preset: str,
    *,
    owner: str | None = None,
    repo: str | None = None,
    query: str | None = None,
    topic: str | None = None,
    extension: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    p = (preset or "").strip().lower().replace("-", "_")
    if p not in PRESETS:
        return {
            "success": False,
            "error": f"Unknown preset. Use one of: {', '.join(PRESETS)}",
        }

    lim = max(1, min(int(limit), 100))

    cap = min(lim, 30)
    plans: dict[str, tuple[tuple[str, dict[str, Any]], ...]] = {
        "org_snapshot": (
            ("Verify GitHub CLI auth", {"operation": "auth_status"}),
            (
                "List repositories for owner",
                {"operation": "repo_list", "owner": owner, "limit": lim},
            ),
        ),
        "topic_hunt": (
            (
                "Search repos by GitHub topic",
                {
                    "operation": "search_repos_topic",
                    "topic": topic,
                    "owner": owner,
                    "query": query,
                    "limit": lim,
                },
            ),
        ),
        "code_sweep": (
            (
                "Code search across scope",
                {
                    "operation": "code_find_repos",
                    "owner": owner,
                    "query": query,
                    "extension": extension,
                    "limit": lim,
                },
            ),
        ),
        "repo_deep_dive": (
            (
                "Repository card (markdown)",
                {
                    "operation": "show_repo",
                    "owner": owner,
                    "repo": repo,
                    "output_format": "markdown",
                },
            ),
            (
                "Open issues snapshot",
                {
                    "operation": "issue_list",
                    "owner": owner,
                    "repo": repo,
                    "state": "open",
                    "limit": cap,
                },
            ),
            (
                "Open pull requests snapshot",
                {
                    "operation": "pr_list",
                    "owner": owner,
                    "repo": repo,
                    "state": "open",
                    "limit": cap,
                },
            ),
            (
                "Gitingest digest URL",
                {"operation": "gitingest_link", "owner": owner, "repo": repo},
            ),
        ),
        "global_search": (
            (
                "Search repositories (global)",
                {"operation": "search_repos", "query": query, "limit": lim},
            ),
        ),
    }

    if p == "org_snapshot" and not owner:
        return {"success": False, "error": "org_snapshot requires owner (user or org)."}
    if p == "topic_hunt" and not topic:
        return {"success": False, "error": "topic_hunt requires topic (GitHub repo topic / tag)."}
    if p == "code_sweep":
        if not owner:
            return {"success": False, "error": "code_sweep requires owner to scope the search."}
        if not query and not extension:
            return {"success": False, "error": "code_sweep requires query and/or extension."}
    if p == "repo_deep_dive" and (not owner or not repo):
        return {"success": False, "error": "repo_deep_dive requires owner and repo."}
    if p == "global_search" and not query:
        return {"success": False, "error": "global_search requires query (GitHub search syntax)."}

    steps_out: list[dict[str, Any]] = []
    for label, spec in plans[p]:
        op = spec.pop("operation")
        result = _call(op, **spec)
        steps_out.append(
            {
                "description": label,
                "operation": op,
                "success": result.get("success", False),
                "result": result,
            }
        )
        if not result.get("success", False):
            return {
                "success": False,
                "preset": p,
                "error": result.get("error", "step failed"),
                "failed_step": len(steps_out),
                "steps": steps_out,
            }

    return {
        "success": True,
        "preset": p,
        "steps_total": len(steps_out),
        "steps": steps_out,
        "hint": (
            "Prefer git_github_search_workflow in MCP clients with full sampling "
            "(e.g. Antigravity) for superior LLM-planned discovery; this run used presets."
        ),
    }
