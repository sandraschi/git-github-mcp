"""Fleet morning digest — open PRs/issues, stale triage, GitHub notifications."""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest

from ..tools.github_ops import github_ops
from ..utils.gh_cli import run_gh
from ..utils.response import error_response, success_response

_SLUG_RE = re.compile(r"^([\w.-]+)/([\w.-]+)$")
_DEFAULT_STATE_DIR = Path(os.getenv("LOCALAPPDATA", Path.home())) / "git-github-mcp"
_STATE_FILE = "last_morning_digest.json"


def parse_fleet_repos(text: str) -> list[tuple[str, str]]:
    """Parse owner/repo lines (same format as web /inbox fleet textarea)."""
    out: list[tuple[str, str]] = []
    for line in text.splitlines():
        t = line.strip()
        if not t or t.startswith("#"):
            continue
        m = _SLUG_RE.match(t)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def default_fleet_repos_file() -> Path:
    env = os.getenv("GIT_GITHUB_FLEET_REPOS_FILE", "").strip()
    if env:
        return Path(env)
    repo_cfg = Path(__file__).resolve().parents[3] / "config" / "fleet-repos.txt"
    if repo_cfg.is_file():
        return repo_cfg
    return _DEFAULT_STATE_DIR / "fleet-repos.txt"


def load_fleet_repos(*, fleet_repos: str | None = None, fleet_repos_file: str | None = None) -> list[tuple[str, str]]:
    if fleet_repos and fleet_repos.strip():
        repos = parse_fleet_repos(fleet_repos)
        if repos:
            return repos
    path = Path(fleet_repos_file) if fleet_repos_file else default_fleet_repos_file()
    if path.is_file():
        return parse_fleet_repos(path.read_text(encoding="utf-8"))
    return []


def _state_path() -> Path:
    custom = os.getenv("GIT_GITHUB_MCP_STATE_DIR", "").strip()
    base = Path(custom) if custom else _DEFAULT_STATE_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base / _STATE_FILE


def _load_state() -> dict[str, Any]:
    path = _state_path()
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_state(payload: dict[str, Any]) -> None:
    path = _state_path()
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _parse_iso(iso: str | None) -> datetime | None:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None


def days_since(iso: str | None) -> int | None:
    dt = _parse_iso(iso)
    if not dt:
        return None
    now = datetime.now(UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return max(0, int((now - dt).total_seconds() // 86400))


def resolve_maintainer_login(override: str | None = None) -> str | None:
    if override and override.strip():
        return override.strip()
    env = os.getenv("GIT_GITHUB_MAINTAINER_LOGIN", "").strip()
    if env:
        return env
    ok, out, _ = run_gh(["api", "user", "-q", ".login"])
    if ok and out.strip():
        return out.strip()
    return None


def _author_login(author: Any) -> str:
    if isinstance(author, dict):
        return str(author.get("login") or "")
    return ""


def _pr_comment_count(raw: Any) -> int:
    """gh pr list --json comments is a list of objects; older callers may pass int."""
    if raw is None:
        return 0
    if isinstance(raw, list):
        return len(raw)
    if isinstance(raw, dict) and "totalCount" in raw:
        try:
            return int(raw["totalCount"])
        except (TypeError, ValueError):
            return 0
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def classify_pr_stale(pr: dict[str, Any], *, stale_days: int, maintainer: str | None) -> str | None:
    """Return stale reason or None if not flagged."""
    author = _author_login(pr.get("author"))
    if maintainer and author.lower() == maintainer.lower():
        return None
    updated = pr.get("updatedAt") or pr.get("createdAt")
    age = days_since(updated)
    if age is None:
        return None
    comments = _pr_comment_count(pr.get("comments"))
    if comments == 0 and age >= stale_days:
        return f"no comments in {age}d"
    if comments > 0 and age >= stale_days:
        return f"quiet {age}d (last activity)"
    return None


def classify_issue_stale(issue: dict[str, Any], *, stale_days: int, maintainer: str | None) -> str | None:
    author = _author_login(issue.get("author"))
    if maintainer and author.lower() == maintainer.lower():
        return None
    updated = issue.get("updatedAt") or issue.get("createdAt")
    age = days_since(updated)
    if age is None:
        return None
    if age >= stale_days:
        return f"open {age}d without maintainer touch"
    return None


def fetch_notifications(*, since_iso: str | None = None) -> list[dict[str, Any]]:
    ok, out, err = run_gh(
        [
            "api",
            "/notifications",
            "-q",
            ".[] | {title, reason, updated_at, unread, "
            "subject_title: .subject.title, subject_url: .subject.url, "
            "repository: .repository.full_name}",
        ],
        timeout=90,
    )
    if not ok:
        return [{"error": err or "notifications fetch failed"}]
    try:
        rows = json.loads(out) if out.strip() else []
    except json.JSONDecodeError:
        return []
    if not isinstance(rows, list):
        return []
    since_dt = _parse_iso(since_iso)
    filtered: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if since_dt:
            row_dt = _parse_iso(row.get("updated_at"))
            if row_dt and row_dt <= since_dt:
                continue
        filtered.append(row)
    return filtered


def scan_fleet_repo(
    owner: str,
    repo: str,
    *,
    stale_days: int,
    maintainer: str | None,
    limit: int,
    include_issues: bool,
) -> dict[str, Any]:
    slug = f"{owner}/{repo}"
    pr_res = github_ops(operation="pr_list", owner=owner, repo=repo, state="open", limit=limit)
    issues_res = (
        github_ops(operation="issue_list", owner=owner, repo=repo, state="open", limit=limit)
        if include_issues
        else {"success": True, "result": {"issues": []}}
    )
    prs = (pr_res.get("result") or {}).get("prs", []) if pr_res.get("success") else []
    issues = (issues_res.get("result") or {}).get("issues", []) if issues_res.get("success") else []
    stale_prs = []
    for pr in prs:
        reason = classify_pr_stale(pr, stale_days=stale_days, maintainer=maintainer)
        if reason:
            stale_prs.append({**pr, "stale_reason": reason, "repo_slug": slug})
    stale_issues = []
    for issue in issues:
        reason = classify_issue_stale(issue, stale_days=stale_days, maintainer=maintainer)
        if reason:
            stale_issues.append({**issue, "stale_reason": reason, "repo_slug": slug})
    return {
        "slug": slug,
        "prs_open": len(prs),
        "issues_open": len(issues),
        "prs": prs,
        "issues": issues,
        "stale_prs": stale_prs,
        "stale_issues": stale_issues,
        "errors": [
            e
            for e in [
                None if pr_res.get("success") else pr_res.get("error"),
                None if issues_res.get("success") else issues_res.get("error"),
            ]
            if e
        ],
    }


def build_markdown_digest(summary: dict[str, Any]) -> str:
    lines = [
        f"# GitHub fleet morning digest",
        f"",
        f"Generated: {summary['generated_at']}",
        f"Maintainer: {summary.get('maintainer') or 'unknown'}",
        f"Repos scanned: {summary['repo_count']}",
        f"",
        f"## Totals",
        f"- Open PRs: **{summary['totals']['open_prs']}**",
        f"- Open issues: **{summary['totals']['open_issues']}**",
        f"- Stale PRs (≥{summary['stale_days']}d): **{summary['totals']['stale_prs']}**",
        f"- Stale issues: **{summary['totals']['stale_issues']}**",
        f"- New notifications: **{summary['totals']['notifications']}**",
        f"",
    ]
    if summary.get("notifications"):
        lines.append("## Notifications (since last run)")
        for n in summary["notifications"][:25]:
            if n.get("error"):
                lines.append(f"- ⚠ {n['error']}")
                continue
            repo = n.get("repository") or "?"
            title = n.get("subject_title") or n.get("title") or "update"
            reason = n.get("reason") or ""
            url = n.get("subject_url") or ""
            unread = "🔴 " if n.get("unread") else ""
            lines.append(f"- {unread}**{repo}** — {title} (`{reason}`) {url}")
        lines.append("")

    stale_prs = summary.get("all_stale_prs") or []
    if stale_prs:
        lines.append(f"## Stale PRs (needs acknowledgment)")
        for pr in stale_prs[:30]:
            lines.append(
                f"- **{pr.get('repo_slug')}** #{pr.get('number')} — {pr.get('title')} "
                f"({pr.get('stale_reason')}) {pr.get('url', '')}"
            )
        lines.append("")

    stale_issues = summary.get("all_stale_issues") or []
    if stale_issues:
        lines.append("## Stale issues")
        for issue in stale_issues[:30]:
            lines.append(
                f"- **{issue.get('repo_slug')}** #{issue.get('number')} — {issue.get('title')} "
                f"({issue.get('stale_reason')}) {issue.get('url', '')}"
            )
        lines.append("")

    if summary.get("repo_errors"):
        lines.append("## Scan errors")
        for err in summary["repo_errors"]:
            lines.append(f"- {err}")
        lines.append("")

    lines.append("---")
    lines.append("Open breakfast: http://127.0.0.1:10703/breakfast")
    return "\n".join(lines)


def _normalize_deliver(deliver: str | list[str] | None) -> list[str]:
    if deliver is None:
        return []
    if isinstance(deliver, str):
        return [d.strip().lower() for d in deliver.split(",") if d.strip()]
    return [str(d).strip().lower() for d in deliver if str(d).strip()]


def _post_json(url: str, body: dict[str, Any], timeout: float = 12.0) -> tuple[bool, str]:
    data = json.dumps(body).encode("utf-8")
    req = urlrequest.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            return True, resp.read().decode("utf-8", errors="replace")[:500]
    except urlerror.URLError as exc:
        return False, str(exc.reason if hasattr(exc, "reason") else exc)


def deliver_digest(markdown: str, summary: dict[str, Any], deliver: list[str]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    if "file" in deliver:
        out_path = Path(
            summary.get("output_file")
            or os.getenv("GIT_GITHUB_DIGEST_OUTPUT", "")
            or (_DEFAULT_STATE_DIR / "morning-digest.md")
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8")
        results["file"] = str(out_path)

    if "aiwatcher" in deliver:
        base = os.getenv("AIWATCHER_HTTP_URL", "http://127.0.0.1:10946").rstrip("/")
        ok, detail = _post_json(
            f"{base}/api/fleet/ingest",
            {
                "title": f"GitHub morning: {summary['totals']['stale_prs']} stale PRs, "
                f"{summary['totals']['notifications']} notifications",
                "summary": markdown[:4000],
                "source": "git-github-mcp",
                "url": "http://127.0.0.1:10703/breakfast",
                "urgency_hint": min(10.0, 3.0 + summary["totals"]["stale_prs"] + summary["totals"]["notifications"] / 5),
            },
        )
        results["aiwatcher"] = {"ok": ok, "detail": detail}

    if "robofang" in deliver:
        base = os.getenv("ROBOFANG_BRIDGE_URL", "http://127.0.0.1:10871").rstrip("/")
        try:
            with urlrequest.urlopen(f"{base}/supervisor/pulse", timeout=8) as resp:
                ping = resp.read().decode("utf-8", errors="replace")[:300]
            results["robofang"] = {
                "ok": True,
                "ping": ping,
                "note": "Bridge reachable; council can read digest from file or aiwatcher ingest",
            }
        except urlerror.URLError as exc:
            reason = str(exc.reason if hasattr(exc, "reason") else exc)
            results["robofang"] = {"ok": False, "error": reason}

    return results


def run_morning_digest(
    *,
    fleet_repos: str | None = None,
    fleet_repos_file: str | None = None,
    stale_days: int | None = None,
    include_issues: bool = True,
    include_notifications: bool = True,
    limit_per_repo: int = 30,
    maintainer_login: str | None = None,
    deliver: str | list[str] | None = None,
    output_file: str | None = None,
    since_last_run: bool = True,
    on_repo_progress: Any = None,
) -> dict[str, Any]:
    """Build fleet morning digest. Callable from MCP tool, HTTP API, or CLI."""
    repos = load_fleet_repos(fleet_repos=fleet_repos, fleet_repos_file=fleet_repos_file)
    if not repos:
        return error_response(
            "fleet_morning_digest",
            "No fleet repos configured. Set fleet_repos text, GIT_GITHUB_FLEET_REPOS_FILE, or config/fleet-repos.txt.",
            recovery_options=[
                "Copy config/fleet-repos.example.txt to config/fleet-repos.txt",
                "Paste owner/repo lines into fleet_repos parameter",
            ],
        )

    stale_n = stale_days if stale_days is not None else int(os.getenv("GIT_GITHUB_STALE_DAYS", "7"))
    maintainer = resolve_maintainer_login(maintainer_login)
    state = _load_state()
    since_iso = state.get("last_run_at") if since_last_run else None

    repo_results: list[dict[str, Any]] = []
    repo_errors: list[str] = []
    all_stale_prs: list[dict[str, Any]] = []
    all_stale_issues: list[dict[str, Any]] = []
    open_prs = 0
    open_issues = 0

    total_repos = len(repos)
    for index, (owner, repo) in enumerate(repos, start=1):
        slug = f"{owner}/{repo}"
        if on_repo_progress:
            on_repo_progress(slug, index, total_repos)
        scanned = scan_fleet_repo(
            owner,
            repo,
            stale_days=stale_n,
            maintainer=maintainer,
            limit=limit_per_repo,
            include_issues=include_issues,
        )
        repo_results.append(scanned)
        open_prs += scanned["prs_open"]
        open_issues += scanned["issues_open"]
        all_stale_prs.extend(scanned["stale_prs"])
        all_stale_issues.extend(scanned["stale_issues"])
        for err in scanned["errors"]:
            repo_errors.append(f"{scanned['slug']}: {err}")

    notifications: list[dict[str, Any]] = []
    if include_notifications:
        notifications = fetch_notifications(since_iso=since_iso)

    all_open_prs: list[dict[str, Any]] = []
    all_open_issues: list[dict[str, Any]] = []
    repo_links: list[dict[str, Any]] = []
    for scanned in repo_results:
        slug = scanned["slug"]
        repo_url = f"https://github.com/{slug}"
        repo_links.append(
            {
                "slug": slug,
                "url": repo_url,
                "open_prs": scanned["prs_open"],
                "open_issues": scanned["issues_open"],
            }
        )
        stale_pr_nums = {int(p.get("number", 0)) for p in scanned["stale_prs"]}
        stale_issue_nums = {int(i.get("number", 0)) for i in scanned["stale_issues"]}
        for pr in scanned["prs"]:
            num = int(pr.get("number", 0))
            row = {
                **pr,
                "repo_slug": slug,
                "repo_url": repo_url,
                "is_stale": num in stale_pr_nums,
            }
            if num in stale_pr_nums:
                for s in scanned["stale_prs"]:
                    if int(s.get("number", 0)) == num:
                        row["stale_reason"] = s.get("stale_reason")
                        break
            all_open_prs.append(row)
        for issue in scanned["issues"]:
            num = int(issue.get("number", 0))
            row = {
                **issue,
                "repo_slug": slug,
                "repo_url": repo_url,
                "is_stale": num in stale_issue_nums,
            }
            if num in stale_issue_nums:
                for s in scanned["stale_issues"]:
                    if int(s.get("number", 0)) == num:
                        row["stale_reason"] = s.get("stale_reason")
                        break
            all_open_issues.append(row)

    def _sort_updated(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        epoch = datetime(1970, 1, 1, tzinfo=UTC)

        return sorted(
            items,
            key=lambda x: _parse_iso(x.get("updatedAt") or x.get("createdAt")) or epoch,
            reverse=True,
        )

    generated_at = datetime.now(UTC).isoformat()
    summary: dict[str, Any] = {
        "generated_at": generated_at,
        "maintainer": maintainer,
        "repo_count": len(repos),
        "stale_days": stale_n,
        "repos": [r["slug"] for r in repo_results],
        "repo_links": repo_links,
        "open_prs": _sort_updated(all_open_prs),
        "open_issues": _sort_updated(all_open_issues),
        "totals": {
            "open_prs": open_prs,
            "open_issues": open_issues,
            "stale_prs": len(all_stale_prs),
            "stale_issues": len(all_stale_issues),
            "notifications": len([n for n in notifications if not n.get("error")]),
        },
        "all_stale_prs": sorted(all_stale_prs, key=lambda p: days_since(p.get("updatedAt")) or 0, reverse=True),
        "all_stale_issues": sorted(
            all_stale_issues, key=lambda i: days_since(i.get("updatedAt")) or 0, reverse=True
        ),
        "notifications": notifications,
        "repo_errors": repo_errors,
        "output_file": output_file,
        "since_last_run": since_iso,
    }
    markdown = build_markdown_digest(summary)
    summary["markdown"] = markdown

    deliver_list = _normalize_deliver(deliver or os.getenv("GIT_GITHUB_DIGEST_DELIVER", ""))
    if deliver_list:
        summary["delivery"] = deliver_digest(markdown, summary, deliver_list)

    _save_state({"last_run_at": generated_at, "repos": len(repos), "totals": summary["totals"]})

    return success_response(
        summary,
        "fleet_morning_digest",
        message=(
            f"Scanned {len(repos)} repos — {summary['totals']['stale_prs']} stale PRs, "
            f"{summary['totals']['notifications']} notifications"
        ),
        next_steps=[
            "Open http://127.0.0.1:10703/breakfast for human triage",
            "Acknowledge stale PRs via github_ops(pr_comment, ...)",
        ],
    )
