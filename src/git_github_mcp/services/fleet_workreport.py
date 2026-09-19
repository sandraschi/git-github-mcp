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
    "_archives",
    "_junk",
    "_upstream",
    "_sandbox_runs",
    "_workspaces",
    "backups",
    "build",
    "data",
    "external",
    "externals",
    "analysis",
    "node_modules",
    ".git",
}
AGENT_TRAILER = "Co-Authored-By: Claude"
RECORD_SEP = "\x1e"
FIELD_SEP = "\x1f"


def _iter_repos(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir() and p.name not in SKIP_DIRS and (p / ".git").exists())


def _commits(repo: Path, since: str, until: str | None) -> list[dict[str, Any]]:
    """One git log call per repo; body included so the agent trailer is visible."""
    args = [
        "log",
        f"--since={since}",
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
        found.append(
            {
                "sha": sha[:8],
                "author": author,
                "at": when,
                "subject": subject.strip(),
                "agent": AGENT_TRAILER.lower() in body.lower(),
            }
        )
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
        by_repo.append(
            {
                "repo": repo.name,
                "commits": len(commits),
                "agentCommits": len(agent),
                "files": files,
                "insertions": plus,
                "deletions": minus,
                "subjects": [c["subject"] for c in shown[:max_subjects]],
                "authors": sorted({c["author"] for c in commits}),
            }
        )
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
        "discordBlocks": render_discord_blocks(by_repo, total_commits, total_agent, since),
    }
    return success_response(
        result,
        "work_report",
        message=(f"{total_commits} commits across {len(by_repo)} repos since {since} ({total_agent} agent-attributed)"),
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


def channel_name_for(repo: str) -> str:
    """The guild's per-repo channel convention: fleet-<name with -mcp stripped>.

    #fleet-arxiv for arxiv-mcp, #fleet-speech for speech-mcp, #fleet-robotics for
    robotics-mcp. Recorded here because it is nowhere else: it has to be inferred by
    reading the channel list against the repo list. Note that only ~40 of the 190+
    repos have a channel, so callers must handle a miss.
    """
    name = repo[:-4] if repo.endswith("-mcp") else repo
    return f"fleet-{name}"


def _repo_block(entry: dict, max_lines: int = 3) -> list[str]:
    """One repo: a header line plus up to max_lines full commit subjects.

    Subjects get their own lines rather than being cut to fit a single line -- a
    subject ending in "..." tells you a commit happened but not what it did, which is
    the one thing the report exists to convey.
    """
    lines = [f"`{entry['repo']}` **{entry['commits']}** (+{entry['insertions']}/-{entry['deletions']})"]
    for subject in entry["subjects"][:max_lines]:
        lines.append(f"  - {subject}")
    remaining = entry["commits"] - min(len(entry["subjects"]), max_lines)
    if remaining > 0:
        lines.append(f"  _+{remaining} more commit{'s' if remaining > 1 else ''}_")
    return lines


def render_discord_blocks(
    by_repo: list[dict],
    commits: int,
    agent: int,
    since: str,
    block_size: int = 20,
    limit: int = 1900,
    max_lines: int = 3,
) -> list[str]:
    """Every repo, alphabetically, split across as many messages as it takes.

    Discord rejects rather than truncates anything over 2000 characters, so the report
    is chunked instead of trimmed: no repo is dropped and no subject is cut. Repos are
    sorted alphabetically (not by commit count) so a given repo lands in a predictable
    message when scanning several days of reports.
    """
    if not by_repo:
        return [f"**Fleet work report** -- no commits since {since}."]

    ordered = sorted(by_repo, key=lambda r: r["repo"].lower())
    chunks = [ordered[i : i + block_size] for i in range(0, len(ordered), block_size)]

    # A block of block_size repos can still exceed the cap once subjects are included,
    # so split any oversized block again rather than emitting something Discord refuses.
    rendered: list[list[str]] = []
    for chunk in chunks:
        current: list[str] = []
        current_len = 0
        for entry in chunk:
            block = _repo_block(entry, max_lines)
            block_len = sum(len(line) + 1 for line in block)
            # 120 chars of headroom for the "[n/m]" header added below.
            if current and current_len + block_len > limit - 120:
                rendered.append(current)
                current, current_len = [], 0
            current.extend(block)
            current_len += block_len
        if current:
            rendered.append(current)

    total = len(rendered)
    messages = []
    for index, body in enumerate(rendered, start=1):
        part = f"  [{index}/{total}]" if total > 1 else ""
        head = (
            f"**Fleet work report** -- {commits} commits / {len(by_repo)} repos since {since}  ({agent} by agent){part}"
        )
        messages.append("\n".join([head, "", *body]))
    return messages


def render_discord(
    by_repo: list[dict], commits: int, agent: int, since: str, block_size: int = 20, limit: int = 1900
) -> str:
    """First message only -- kept for callers that want a single string."""
    return render_discord_blocks(by_repo, commits, agent, since, block_size, limit)[0]


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
        return {"success": False, "error": f"HTTP {exc.code}", "detail": exc.read().decode("utf-8", "replace")[:300]}
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return {"success": False, "error": str(exc)}


def post_to_discord_blocks(
    messages: list[str], channel_id: str, token: str | None = None, pause_seconds: float = 1.2
) -> dict[str, Any]:
    """Send a multi-part report in order, stopping at the first failure.

    Discord rate-limits bots to roughly 5 messages per 5 seconds per channel, so parts
    are paced. Sending stops on the first failure rather than continuing, because a
    report missing its middle is worse than one that visibly ends early.
    """
    import time

    sent, failures = [], []
    for index, message in enumerate(messages):
        if index:
            time.sleep(pause_seconds)
        outcome = post_to_discord(message, channel_id, token=token)
        if outcome.get("success"):
            sent.append(outcome.get("messageId"))
        else:
            failures.append({"part": index + 1, **outcome})
            break
    return {
        "success": not failures,
        "parts": len(messages),
        "sent": sent,
        "failures": failures,
        "channelId": channel_id,
    }
