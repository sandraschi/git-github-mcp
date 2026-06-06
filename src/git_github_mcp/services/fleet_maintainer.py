"""Fleet maintainer — mention inbox, acknowledgment drafts."""

from __future__ import annotations

from typing import Any

from ..utils.response import success_response
from .fleet_catalog import registry_to_github_slugs, load_registry
from .morning_digest import (
    classify_pr_stale,
    fetch_notifications,
    resolve_maintainer_login,
    scan_fleet_repo,
)
from .fleet_health import _resolve_repos

_MENTION_REASONS = frozenset(
    {
        "mention",
        "assign",
        "author",
        "review_requested",
        "team_mention",
        "subscribed",
        "participating",
    }
)

_ACK_TEMPLATE = (
    "Thanks for the PR — I maintain this in spare time and do not always see notifications quickly. "
    "I have read it and will review properly within the next few days; I will comment here if I need changes."
)


def op_mention_inbox(
    *,
    fleet_repos: str | None = None,
    since_last_run: bool = True,
    reasons: list[str] | None = None,
) -> dict[str, Any]:
    allowed = set(reasons) if reasons else _MENTION_REASONS
    since_iso = None
    if since_last_run:
        from .morning_digest import _load_state

        since_iso = (_load_state() or {}).get("last_run_at")
    rows = fetch_notifications(since_iso=since_iso)
    filtered: list[dict[str, Any]] = []
    for row in rows:
        if row.get("error"):
            continue
        reason = str(row.get("reason") or "").lower()
        if reason in allowed or not reasons:
            repo = row.get("repository") or ""
            filtered.append(
                {
                    **row,
                    "repo_url": f"https://github.com/{repo}" if repo else None,
                }
            )
    return success_response(
        {"count": len(filtered), "notifications": filtered, "since": since_iso},
        "mention_inbox",
        message=f"{len(filtered)} mention/review notifications",
    )


def op_ack_drafts(
    *,
    fleet_repos: str | None = None,
    fleet_repos_file: str | None = None,
    use_registry: bool = False,
    stale_days: int = 7,
    maintainer_login: str | None = None,
    template: str | None = None,
) -> dict[str, Any]:
    repos = _resolve_repos(
        fleet_repos=fleet_repos, fleet_repos_file=fleet_repos_file, use_registry=use_registry
    )
    maintainer = resolve_maintainer_login(maintainer_login)
    body_template = (template or _ACK_TEMPLATE).strip()
    drafts: list[dict[str, Any]] = []

    for owner, repo in repos:
        scanned = scan_fleet_repo(
            owner, repo, stale_days=stale_days, maintainer=maintainer, limit=30, include_issues=False
        )
        for pr in scanned["stale_prs"]:
            drafts.append(
                {
                    "repo_slug": scanned["slug"],
                    "repo_url": f"https://github.com/{scanned['slug']}",
                    "pr_number": pr.get("number"),
                    "title": pr.get("title"),
                    "url": pr.get("url"),
                    "stale_reason": pr.get("stale_reason"),
                    "draft_body": body_template,
                    "github_ops_hint": (
                        f"github_ops(operation='pr_comment', owner='{owner}', repo='{repo}', "
                        f"pr_number={pr.get('number')}, body='...')"
                    ),
                }
            )

    return success_response(
        {"count": len(drafts), "drafts": drafts, "template": body_template},
        "ack_drafts",
        message=f"{len(drafts)} acknowledgment drafts for stale PRs",
    )
