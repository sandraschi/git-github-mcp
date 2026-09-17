"""Fleet work report -- what actually changed, and who changed it.

Every other fleet report answers "what is broken right now": ci_pulse, port_audit,
local_dirty, release_drift, and the morning digest all describe current state. None of
them answer "what was done today", which is the question you ask at the end of a day or
when picking up someone else's thread.

The data needs no new bookkeeping. Claude Code appends a `Co-Authored-By: Claude`
trailer to every commit it makes, so agent work is already separable from hand work by
reading git log -- nothing to keep in sync, nothing that can drift out of date.

Known limits, so the numbers are not over-read:
  - It counts COMMITS, not work. Registering a scheduled task, restarting a service or
    syncing a manifest leaves no commit and will not appear here.
  - Vendored and bulk-sweep commits inflate totals; `by_repo` is more honest than the
    grand total.
  - Only local repos are scanned. Work pushed from elsewhere is invisible until pulled.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from ..utils.response import success_response
from .fleet_common import DEFAULT_REPOS_ROOT, run_git

SKIP_DIRS = {
    "_archives", "_junk", "_upstream", "_sandbox_runs", "_workspaces", "backups",
    "build", "data", "external", "externals", "analysis", "node_modules", ".git",
}
AGENT_TRAILER = "Co-Authored-By: Claude"
RECORD_SEP = "\x1e"
FIELD_SEP = "\x1f"


def _iter_repos(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        p for p in root.iterdir()
        if p.is_dir() and p.name not in SKIP_DIRS and (p / ".git").exists()
    )


def _commits(repo: Path, since: str, until: str | None) -> list[dict[str, Any]]:
    """One git log call per repo; body included so the agent trailer is visible."""
    args = [
        "log", f"--since={since}",
        f"--pretty=format:%H{FIELD_SEP}%an{FIELD_SEP}%aI{FIELD_SEP}%s{FIELD_SEP}%b{RECORD_SEP}",
        "--no-merges",
    ]
    if until:
        args.insert(2, f"--until={until}")
    ok, out, _ = run_git(args, repo, timeout=60)
    if not ok or not out.strip():
        return []

    found = []
    for chunk in out.split(RECORD_SEP):
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        parts = chunk.split(FIELD_SEP)
        if len(parts) < 4:
            continue
        sha, author, when, subject = parts[0], parts[1], parts[2], parts[3]
        body = parts[4] if len(parts) > 4 else ""
        found.append({
            "sha": sha[:8],
            "author": author,
            "at": when,
            "subject": subject.strip(),
            "agent": AGENT_TRAILER.lower() in body.lower(),
        })
    return found


def _churn(repo: Path, since: str, until: str | None) -> tuple[int, int, int]:
    """(files, insertions, deletions) over the window."""
    args = ["log", f"--since={since}", "--no-merges", "--numstat", "--format="]
    if until:
        args.insert(2, f"--until={until}")
    ok, out, _ = run_git(args, repo, timeout=60)
    if not ok:
        return (0, 0, 0)
    files, plus, minus = set(), 0, 0
    for line in out.splitlines():
        cols = line.split("\t")
        if len(cols) != 3:
            continue
        added, removed, path = cols
        files.add(path)
        # Binary files report "-" rather than a count.
        plus += int(added) if added.isdigit() else 0
        minus += int(removed) if removed.isdigit() else 0
    return (len(files), plus, minus)


def op_work_report(
    *,
    repos_root: str | None = None,
    since: str = "midnight",
    until: str | None = None,
    agent_only: bool = False,
    max_subjects: int = 4,
) -> dict[str, Any]:
    """Summarise what changed across the fleet in a time window."""
    root = Path(repos_root) if repos_root else DEFAULT_REPOS_ROOT
    by_repo: list[dict[str, Any]] = []
    total_commits = total_agent = 0
    total_files = total_plus = total_minus = 0

    for repo in _iter_repos(root):
        commits = _commits(repo, since, until)
        if not commits:
            continue
        agent = [c for c in commits if c["agent"]]
        if agent_only and not agent:
            continue
        files, plus, minus = _churn(repo, since, until)
        shown = agent if agent_only else commits
        by_repo.append({
            "repo": repo.name,
            "commits": len(commits),
            "agentCommits": len(agent),
            "files": files,
            "insertions": plus,
            "deletions": minus,
            "subjects": [c["subject"] for c in shown[:max_subjects]],
            "authors": sorted({c["author"] for c in commits}),
        })
        total_commits += len(commits)
        total_agent += len(agent)
        total_files += files
        total_plus += plus
        total_minus += minus

    by_repo.sort(key=lambda r: (-r["commits"], r["repo"]))
    result = {
        "generatedAt": datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"),
        "window": {"since": since, "until": until or "now"},
        "reposRoot": str(root),
        "totals": {
            "repos": len(by_repo),
            "commits": total_commits,
            "agentCommits": total_agent,
            "humanCommits": total_commits - total_agent,
            "filesChanged": total_files,
            "insertions": total_plus,
            "deletions": total_minus,
        },
        "byRepo": by_repo,
        "markdown": render_markdown(by_repo, total_commits, total_agent, since),
        "discord": render_discord(by_repo, total_commits, total_agent, since),
    }
    return success_response(
        result,
        "work_report",
        message=(f"{total_commits} commits across {len(by_repo)} repos since {since} "
                 f"({total_agent} agent-attributed)"),
    )


def render_markdown(by_repo: list[dict], commits: int, agent: int, since: str) -> str:
    lines = [
        f"# Fleet work report -- since {since}",
        "",
        f"**{commits} commits** across **{len(by_repo)} repos** "
        f"({agent} agent-attributed, {commits - agent} hand-written)",
        "",
        "| Repo | Commits | Agent | Files | +/- |",
        "|---|---|---|---|---|",
    ]
    for entry in by_repo:
        lines.append(
            f"| `{entry['repo']}` | {entry['commits']} | {entry['agentCommits']} | "
            f"{entry['files']} | +{entry['insertions']}/-{entry['deletions']} |"
        )
    lines.append("")
    for entry in by_repo:
        lines.append(f"**{entry['repo']}**")
        for subject in entry["subjects"]:
            lines.append(f"  - {subject}")
        remaining = entry["commits"] - len(entry["subjects"])
        if remaining > 0:
            lines.append(f"  - ... and {remaining} more")
        lines.append("")
    return "\n".join(lines)


def render_discord(by_repo: list[dict], commits: int, agent: int, since: str,
                   top: int = 8, limit: int = 1900) -> str:
    """Compact enough for a channel: headline, top repos, one line each.

    Discord hard-caps content at 2000 characters and rejects (never truncates) anything
    longer, so this stays deliberately terse and is clamped before it is sent.
    """
    if not by_repo:
        return f"**Fleet work report** -- no commits since {since}."

    head = (f"**Fleet work report** -- {commits} commits / {len(by_repo)} repos "
            f"since {since}  ({agent} by agent)")
    lines = [head, ""]
    for entry in by_repo[:top]:
        headline = entry["subjects"][0] if entry["subjects"] else ""
        if len(headline) > 72:
            headline = headline[:69] + "..."
        lines.append(
            f"`{entry['repo']}` **{entry['commits']}** "
            f"(+{entry['insertions']}/-{entry['deletions']}) - {headline}"
        )
    if len(by_repo) > top:
        lines.append(f"_...and {len(by_repo) - top} more repos_")

    text = "\n".join(lines)
    if len(text) > limit:
        text = text[:limit].rsplit("\n", 1)[0] + "\n_...truncated_"
    return text


def post_to_discord(content: str, channel_id: str, token: str | None = None) -> dict[str, Any]:
    """Send one message via the Discord REST API.

    Deliberately a direct REST call rather than a discord-mcp tool call: that server's
    portmanteau currently declares all 38 parameters non-optional, so a caller must pass
    every one of them, and its card tools raise on an unexpected 'structured' kwarg.
    """
    import json
    import urllib.error
    import urllib.request

    bot_token = token or os.getenv("DISCORD_TOKEN", "")
    if not bot_token:
        return {"success": False, "error": "DISCORD_TOKEN not set"}
    if len(content) > 2000:
        return {"success": False, "error": f"content is {len(content)} chars, Discord caps at 2000"}

    request = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{channel_id}/messages",
        data=json.dumps({"content": content}).encode(),
        headers={
            "Authorization": f"Bot {bot_token}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (fleet-workreport, 1.0)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8", "replace"))
            return {"success": True, "messageId": payload.get("id"), "channelId": channel_id}
    except urllib.error.HTTPError as exc:
        return {"success": False, "error": f"HTTP {exc.code}",
                "detail": exc.read().decode("utf-8", "replace")[:300]}
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return {"success": False, "error": str(exc)}
