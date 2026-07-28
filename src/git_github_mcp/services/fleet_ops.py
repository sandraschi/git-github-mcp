"""Fleet operations portmanteau — all fleet-specific maintainer tools."""

from __future__ import annotations

from typing import Any

from ..utils.response import error_response
from .fleet_catalog import op_docs_gate, op_port_audit, op_quarantine_report, op_registry_load
from .fleet_health import op_ci_pulse, op_dependabot_digest
from .fleet_links import op_gitingest_bundle, op_grade_snapshot
from .fleet_maintainer import op_ack_drafts, op_mention_inbox
from .fleet_orchestrator import op_council_payload, op_runner_status, op_weekly_retro, run_full_suite
from .fleet_workspace import op_local_dirty, op_release_drift

OPERATIONS = frozenset(
    {
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
    }
)


def fleet_ops(
    operation: str,
    *,
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
    suite_json: dict[str, Any] | None = None,
    template: str | None = None,
) -> dict[str, Any]:
    """Fleet maintainer operations for sandraschi MCP fleet."""
    op = (operation or "").strip().lower()
    if op not in OPERATIONS:
        return error_response(
            "fleet_ops",
            f"Unknown operation: {operation}",
            recovery_options=[f"Valid: {', '.join(sorted(OPERATIONS))}"],
        )

    common = {
        "fleet_repos": fleet_repos,
        "fleet_repos_file": fleet_repos_file,
        "use_registry": use_registry,
    }

    if op == "registry_load":
        return op_registry_load(registry_path=registry_path, owner=owner or "sandraschi")
    if op == "port_audit":
        return op_port_audit(registry_path=registry_path)
    if op == "docs_gate":
        return op_docs_gate(registry_path=registry_path, repos_root=repos_root)
    if op == "quarantine_report":
        return op_quarantine_report(registry_path=registry_path, owner=owner or "sandraschi")
    if op == "ci_pulse":
        return op_ci_pulse(**common, hours=hours)
    if op == "dependabot_digest":
        return op_dependabot_digest(**common)
    if op == "mention_inbox":
        return op_mention_inbox(fleet_repos=fleet_repos, since_last_run=since_last_run)
    if op == "ack_drafts":
        return op_ack_drafts(
            **common,
            stale_days=stale_days,
            maintainer_login=maintainer_login,
            template=template,
        )
    if op == "local_dirty":
        return op_local_dirty(
            registry_path=registry_path,
            repos_root=repos_root,
            fleet_repos=fleet_repos,
            use_registry=use_registry,
        )
    if op == "release_drift":
        return op_release_drift(**common, repos_root=repos_root)
    if op == "grade_snapshot":
        return op_grade_snapshot(owner=owner or "sandraschi", scraper_url=scraper_url)
    if op == "gitingest_bundle":
        return op_gitingest_bundle(**common)
    if op == "runner_status":
        return op_runner_status()
    if op == "weekly_retro":
        return op_weekly_retro(fleet_repos=fleet_repos, use_registry=use_registry, days=days)
    if op == "council_payload":
        return op_council_payload(suite_json or {})
    if op == "full_suite":
        return run_full_suite(
            fleet_repos=fleet_repos,
            fleet_repos_file=fleet_repos_file,
            use_registry=use_registry,
            stale_days=stale_days,
            deliver=deliver,
            maintainer_login=maintainer_login,
            since_last_run=since_last_run,
        )

    return error_response("fleet_ops", "Unhandled operation")
