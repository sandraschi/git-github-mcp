"""GitHub operations portmanteau via gh CLI."""

import json
from pathlib import Path
from typing import Any

from ..utils.gh_cli import run_gh
from ..utils.response import success_response, error_response


def github_ops(
    operation: str,
    owner: str | None = None,
    repo: str | None = None,
    title: str | None = None,
    body: str | None = None,
    issue_number: int | None = None,
    pr_number: int | None = None,
    query: str | None = None,
    state: str = "open",
    limit: int = 10,
) -> dict[str, Any]:
    """GitHub operations: create_issue, list_issues, create_pr, list_prs, search."""
    ops = {"create_issue", "list_issues", "create_pr", "list_prs", "search"}
    if operation not in ops:
        return error_response(
            operation,
            f"Unknown operation. Use one of: {', '.join(sorted(ops))}",
            suggested_fixes=["github_ops(operation='list_issues', owner='...', repo='...')"],
        )

    if operation in ("create_issue", "list_issues", "create_pr", "list_prs") and not (owner and repo):
        return error_response(
            operation,
            "owner and repo required",
            suggested_fixes=["Set owner and repo (e.g. openclaw, openclaw)"],
        )

    if operation == "create_issue":
        if not title:
            return error_response(operation, "title required")
        args = ["issue", "create", "--repo", f"{owner}/{repo}", "--title", title]
        if body:
            args.extend(["--body", body])
        ok, out, err = run_gh(args)
        if not ok:
            return error_response(
                operation,
                err or "Create issue failed",
                recovery_options=["gh auth login", "Check repo access"],
            )
        return success_response(
            {"url": out.strip(), "title": title},
            operation,
            message="Issue created",
            next_steps=[f"github_ops(operation='list_issues', owner='{owner}', repo='{repo}')"],
        )

    if operation == "list_issues":
        args = [
            "issue", "list",
            "--repo", f"{owner}/{repo}",
            "--state", state,
            "--limit", str(limit),
            "--json", "number,title,state,url",
        ]
        ok, out, err = run_gh(args)
        if not ok:
            return error_response(operation, err or "List issues failed")
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            data = []
        return success_response(
            {"issues": data, "count": len(data)},
            operation,
            next_steps=[f"github_ops(operation='create_issue', owner='{owner}', repo='{repo}', title='...')"],
        )

    if operation == "create_pr":
        if not title:
            return error_response(operation, "title required")
        args = ["pr", "create", "--repo", f"{owner}/{repo}", "--title", title]
        if body:
            args.extend(["--body", body])
        ok, out, err = run_gh(args)
        if not ok:
            return error_response(
                operation,
                err or "Create PR failed",
                recovery_options=["Check branch pushed", "gh auth login"],
            )
        return success_response(
            {"url": out.strip(), "title": title},
            operation,
            message="PR created",
            next_steps=[f"github_ops(operation='list_prs', owner='{owner}', repo='{repo}')"],
        )

    if operation == "list_prs":
        args = [
            "pr", "list",
            "--repo", f"{owner}/{repo}",
            "--state", state,
            "--limit", str(limit),
            "--json", "number,title,state,url",
        ]
        ok, out, err = run_gh(args)
        if not ok:
            return error_response(operation, err or "List PRs failed")
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            data = []
        return success_response(
            {"prs": data, "count": len(data)},
            operation,
        )

    if operation == "search":
        if not query:
            return error_response(operation, "query required for search")
        args = [
            "search", "repos", query,
            "--limit", str(limit),
            "--json", "name,fullName,description,url",
        ]
        ok, out, err = run_gh(args)
        if not ok:
            return error_response(operation, err or "Search failed")
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            data = []
        return success_response(
            {"repos": data, "count": len(data)},
            operation,
        )

    return error_response(operation, "Not implemented")
