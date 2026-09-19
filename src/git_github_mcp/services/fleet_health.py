"""Fleet health — CI pulse, Dependabot / security digest."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from ..tools.github_ops import github_ops
from ..utils.gh_cli import run_gh
from ..utils.response import success_response
from .fleet_catalog import load_registry, registry_to_github_slugs
from .fleet_common import load_fleet_repos, parse_iso


def _resolve_repos(
    *,
    fleet_repos: str | None = None,
    fleet_repos_file: str | None = None,
    use_registry: bool = False,
) -> list[tuple[str, str]]:
    if use_registry:
        return registry_to_github_slugs(load_registry())
    repos = load_fleet_repos(fleet_repos=fleet_repos, fleet_repos_file=fleet_repos_file)
    return repos if repos else registry_to_github_slugs(load_registry())


# Cap on per-failure `gh run view` lookups per scan. Reasons are best-effort
# enrichment; a pathological scan with dozens of failures must not turn into
# dozens of extra API calls.
_MAX_FAILURE_REASONS = 10


def _failed_jobs_summary(jobs: Any) -> list[dict[str, Any]]:
    """Failed jobs/steps extracted from `gh run view --json jobs` output."""
    summary: list[dict[str, Any]] = []
    if not isinstance(jobs, list):
        return summary
    for job in jobs:
        if not isinstance(job, dict):
            continue
        if str(job.get("conclusion") or "").lower() not in ("failure", "cancelled", "timed_out"):
            continue
        steps = [
            str(step.get("name") or "")
            for step in (job.get("steps") or [])
            if isinstance(step, dict) and str(step.get("conclusion") or "").lower() == "failure"
        ]
        summary.append({"job": job.get("name"), "failed_steps": steps})
    return summary


def _failure_reason_text(failed_jobs: list[dict[str, Any]]) -> str:
    parts = []
    for entry in failed_jobs:
        steps = ", ".join(s for s in entry.get("failed_steps", []) if s)
        parts.append(f"job '{entry.get('job')}'" + (f" steps: {steps}" if steps else ""))
    return "; ".join(parts)


def op_ci_pulse(
    *,
    fleet_repos: str | None = None,
    fleet_repos_file: str | None = None,
    use_registry: bool = False,
    hours: int = 48,
    limit_per_repo: int = 8,
    on_repo_progress: Any = None,
) -> dict[str, Any]:
    repos = _resolve_repos(fleet_repos=fleet_repos, fleet_repos_file=fleet_repos_file, use_registry=use_registry)
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    failures: list[dict[str, Any]] = []
    scanned = 0
    errors: list[str] = []
    reason_lookups = 0
    reasons_capped = False

    total = len(repos)
    for index, (owner, repo) in enumerate(repos, start=1):
        slug = f"{owner}/{repo}"
        if on_repo_progress:
            on_repo_progress(slug, index, total)
        res = github_ops(operation="workflow_runs", owner=owner, repo=repo, limit=limit_per_repo)
        scanned += 1
        if not res.get("success"):
            errors.append(f"{slug}: {res.get('error')}")
            continue
        runs = (res.get("result") or {}).get("runs") or []
        for run in runs:
            if not isinstance(run, dict):
                continue
            conclusion = str(run.get("conclusion") or "").lower()
            if conclusion not in ("failure", "cancelled", "timed_out"):
                continue
            created = parse_iso(run.get("createdAt"))
            if created and created < cutoff:
                continue
            entry: dict[str, Any] = {
                "repo_slug": slug,
                "repo_url": f"https://github.com/{slug}",
                "name": run.get("name"),
                "conclusion": conclusion,
                "status": run.get("status"),
                "branch": run.get("headBranch"),
                "created_at": run.get("createdAt"),
                "url": run.get("url"),
                "failed_jobs": [],
                "failure_reason": "",
            }
            run_id = run.get("databaseId")
            if run_id is not None and reason_lookups < _MAX_FAILURE_REASONS:
                reason_lookups += 1
                ok2, jobs_out, _ = run_gh(
                    ["run", "view", str(run_id), "--repo", slug, "--json", "jobs", "-q", ".jobs"],
                    timeout=30,
                )
                if ok2 and jobs_out.strip():
                    try:
                        failed = _failed_jobs_summary(json.loads(jobs_out))
                    except json.JSONDecodeError:
                        failed = []
                    entry["failed_jobs"] = failed
                    entry["failure_reason"] = _failure_reason_text(failed)
            elif run_id is not None:
                reasons_capped = True
            failures.append(entry)

    failures.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return success_response(
        {
            "hours": hours,
            "repos_scanned": scanned,
            "failure_count": len(failures),
            "failures": failures,
            "errors": errors,
            "reason_lookups": reason_lookups,
            "reasons_capped": reasons_capped,
        },
        "ci_pulse",
        message=f"{len(failures)} failed workflow runs in last {hours}h",
    )


def _dependabot_alerts(owner: str, repo: str) -> list[dict[str, Any]]:
    slug = f"{owner}/{repo}"
    ok, out, err = run_gh(
        [
            "api",
            f"repos/{slug}/dependabot/alerts",
            "-q",
            ".[] | {number, state, security_advisory: .security_advisory.severity, "
            "package: .dependency.package.name, url: .html_url, created_at: .created_at}",
        ],
        timeout=45,
    )
    if not ok:
        return [{"error": err or "dependabot fetch failed", "repo_slug": slug}]
    try:
        rows = json.loads(out) if out.strip() else []
    except json.JSONDecodeError:
        return []
    if not isinstance(rows, list):
        return []
    for row in rows:
        if isinstance(row, dict):
            row["repo_slug"] = slug
            row["repo_url"] = f"https://github.com/{slug}"
    return rows


def op_dependabot_digest(
    *,
    fleet_repos: str | None = None,
    fleet_repos_file: str | None = None,
    use_registry: bool = False,
    open_only: bool = True,
    on_repo_progress: Any = None,
) -> dict[str, Any]:
    repos = _resolve_repos(fleet_repos=fleet_repos, fleet_repos_file=fleet_repos_file, use_registry=use_registry)
    all_alerts: list[dict[str, Any]] = []
    errors: list[str] = []
    total = len(repos)
    for index, (owner, repo) in enumerate(repos, start=1):
        slug = f"{owner}/{repo}"
        if on_repo_progress:
            on_repo_progress(slug, index, total)
        rows = _dependabot_alerts(owner, repo)
        for row in rows:
            if row.get("error"):
                errors.append(f"{row.get('repo_slug')}: {row['error']}")
                continue
            if open_only and str(row.get("state") or "").lower() not in ("open", ""):
                continue
            all_alerts.append(row)

    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_alerts.sort(
        key=lambda a: severity_rank.get(str(a.get("security_advisory") or a.get("severity") or "").lower(), 9)
    )
    return success_response(
        {
            "repos_scanned": len(repos),
            "alert_count": len(all_alerts),
            "alerts": all_alerts,
            "errors": errors,
        },
        "dependabot_digest",
        message=f"{len(all_alerts)} open Dependabot/security alerts across fleet",
    )
