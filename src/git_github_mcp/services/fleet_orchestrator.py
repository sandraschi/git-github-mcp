"""Fleet orchestrator — runner status, council payload, weekly retro, full suite."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ..tools.github_ops import github_ops
from ..utils.gh_cli import run_gh
from ..utils.response import success_response
from .fleet_catalog import op_docs_gate, op_port_audit, op_quarantine_report, op_registry_load
from .fleet_common import DEFAULT_FLEET_OWNER, state_dir
from .fleet_health import op_ci_pulse, op_dependabot_digest
from .fleet_links import op_gitingest_bundle, op_grade_snapshot
from .fleet_maintainer import op_ack_drafts, op_mention_inbox
from .fleet_workspace import op_local_dirty, op_release_drift
from .morning_digest import run_morning_digest

_TASK_NAME = "GitHub-Fleet-Morning-Digest"


def op_runner_status() -> dict[str, Any]:
    state_path = state_dir() / "last_morning_digest.json"
    state: dict[str, Any] = {}
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            state = {}

    scheduled: dict[str, Any] = {"installed": False}
    if os.name == "nt":
        try:
            result = subprocess.run(
                ["schtasks", "/Query", "/TN", _TASK_NAME, "/FO", "LIST"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
                creationflags=0x08000000,
            )
            if result.returncode == 0:
                scheduled["installed"] = True
                scheduled["raw"] = result.stdout[:1500]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            scheduled["installed"] = False

    digest_file = state_dir() / "morning-digest.md"
    return success_response(
        {
            "last_run_at": state.get("last_run_at"),
            "last_totals": state.get("totals"),
            "scheduled_task": scheduled,
            "digest_file": str(digest_file) if digest_file.is_file() else None,
            "state_file": str(state_path),
        },
        "runner_status",
        message="Breakfast runner status",
    )


def op_weekly_retro(
    *,
    fleet_repos: str | None = None,
    use_registry: bool = True,
    days: int = 7,
) -> dict[str, Any]:
    from .fleet_health import _resolve_repos

    repos = _resolve_repos(fleet_repos=fleet_repos, use_registry=use_registry)
    since = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%d")
    merged_prs: list[dict[str, Any]] = []
    new_issues: list[dict[str, Any]] = []

    for owner, repo in repos[:40]:
        slug = f"{owner}/{repo}"
        q_prs = f"repo:{slug} is:pr is:merged merged:>{since}"
        ok, out, _ = run_gh(
            ["search", "prs", q_prs, "--limit", "10", "--json", "number,title,url,mergedAt,author"],
            timeout=60,
        )
        if ok and out.strip():
            try:
                for row in json.loads(out):
                    if isinstance(row, dict):
                        row["repo_slug"] = slug
                        merged_prs.append(row)
            except json.JSONDecodeError:
                pass
        q_issues = f"repo:{slug} is:issue created:>{since}"
        ok2, out2, _ = run_gh(
            ["search", "issues", q_issues, "--limit", "10", "--json", "number,title,url,createdAt,author"],
            timeout=60,
        )
        if ok2 and out2.strip():
            try:
                for row in json.loads(out2):
                    if isinstance(row, dict):
                        row["repo_slug"] = slug
                        new_issues.append(row)
            except json.JSONDecodeError:
                pass

    return success_response(
        {
            "days": days,
            "since": since,
            "merged_pr_count": len(merged_prs),
            "new_issue_count": len(new_issues),
            "merged_prs": merged_prs[:50],
            "new_issues": new_issues[:50],
        },
        "weekly_retro",
        message=f"Last {days}d: {len(merged_prs)} merged PRs, {len(new_issues)} new issues",
    )


def op_council_payload(suite: dict[str, Any]) -> dict[str, Any]:
    """Structure breakfast + fleet checks for robofang / supervisor agents."""
    digest = suite.get("morning_digest") or {}
    result = digest.get("result") if isinstance(digest, dict) else {}
    totals = (result or {}).get("totals") or {}
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "kind": "github_fleet_maintainer",
        "summary": {
            "stale_prs": totals.get("stale_prs", 0),
            "notifications": totals.get("notifications", 0),
            "ci_failures": (suite.get("ci_pulse") or {}).get("result", {}).get("failure_count", 0),
            "dependabot_alerts": (suite.get("dependabot_digest") or {}).get("result", {}).get("alert_count", 0),
            "dirty_repos": (suite.get("local_dirty") or {}).get("result", {}).get("dirty_count", 0),
            "port_collisions": (suite.get("port_audit") or {}).get("result", {}).get("collision_count", 0),
        },
        "actions": [
            "Review stale PRs and post acknowledgments",
            "Triage CI failures and Dependabot alerts",
            "Fix port collisions and docs_gate gaps",
        ],
        "suite": suite,
    }
    return success_response(payload, "council_payload", message="Structured fleet maintainer payload")


def run_full_suite(
    *,
    fleet_repos: str | None = None,
    fleet_repos_file: str | None = None,
    use_registry: bool = True,
    stale_days: int = 7,
    deliver: str | list[str] | None = None,
    maintainer_login: str | None = None,
    since_last_run: bool = True,
) -> dict[str, Any]:
    if use_registry and not fleet_repos:
        reg = op_registry_load()
        if reg.get("success"):
            fleet_repos = (reg.get("result") or {}).get("fleet_repos_text")

    common = {
        "fleet_repos": fleet_repos,
        "fleet_repos_file": fleet_repos_file,
        "use_registry": use_registry,
    }

    suite: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "morning_digest": run_morning_digest(
            fleet_repos=fleet_repos,
            fleet_repos_file=fleet_repos_file,
            stale_days=stale_days,
            deliver=deliver,
            maintainer_login=maintainer_login,
            since_last_run=since_last_run,
        ),
        "registry_load": op_registry_load(),
        "mention_inbox": op_mention_inbox(since_last_run=since_last_run),
        "ci_pulse": op_ci_pulse(**common),
        "dependabot_digest": op_dependabot_digest(**common),
        "ack_drafts": op_ack_drafts(
            fleet_repos=fleet_repos,
            fleet_repos_file=fleet_repos_file,
            use_registry=use_registry,
            stale_days=stale_days,
            maintainer_login=maintainer_login,
        ),
        "port_audit": op_port_audit(),
        "docs_gate": op_docs_gate(),
        "quarantine_report": op_quarantine_report(),
        "local_dirty": op_local_dirty(use_registry=use_registry),
        "release_drift": op_release_drift(**common),
        "grade_snapshot": op_grade_snapshot(owner=DEFAULT_FLEET_OWNER),
        "gitingest_bundle": op_gitingest_bundle(**common),
        "runner_status": op_runner_status(),
        "weekly_retro": op_weekly_retro(fleet_repos=fleet_repos, use_registry=use_registry),
    }
    suite["council_payload"] = op_council_payload(suite)
    return success_response(suite, "full_suite", message="Full fleet maintainer suite completed")
