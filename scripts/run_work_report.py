"""CLI entry for the fleet work report -- what changed today, and who changed it.

Mirrors run_morning_digest.py: the digest says what is broken, this says what was done.

    python scripts/run_work_report.py --since midnight
    python scripts/run_work_report.py --since "3 days ago" --agent-only
    python scripts/run_work_report.py --channel 1532746583073099969 --out worklog.md
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from git_github_mcp.services.fleet_workreport import (
    op_work_report,
    post_to_discord,
)

# Windows consoles and Task Scheduler default to cp1252 and cannot encode the arrows
# and dashes in commit subjects. Printing raised UnicodeEncodeError and the scheduled
# morning digest exited non-zero for weeks despite having done its work; do not repeat it.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def load_token() -> str:
    """DISCORD_TOKEN from the environment, else discord-mcp's .env."""
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if token:
        return token
    env_file = Path(os.getenv("FLEET_REPOS_ROOT", r"D:\Dev\repos")) / "discord-mcp" / ".env"
    if not env_file.is_file():
        return ""
    for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().startswith("DISCORD_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Fleet work report")
    parser.add_argument("--since", default="midnight",
                        help="git --since expression (default: midnight)")
    parser.add_argument("--until", default=None)
    parser.add_argument("--repos-root", default=None)
    parser.add_argument("--agent-only", action="store_true",
                        help="only repos with agent-attributed commits")
    parser.add_argument("--channel", default=None,
                        help="Discord channel id to post the compact report to")
    parser.add_argument("--out", default=None, help="write the full markdown here")
    parser.add_argument("--quiet", action="store_true",
                        help="do not print the report body")
    args = parser.parse_args()

    report = op_work_report(
        repos_root=args.repos_root,
        since=args.since,
        until=args.until,
        agent_only=args.agent_only,
    )
    if not report.get("success"):
        print(report.get("error") or "work report failed", file=sys.stderr)
        return 1

    payload = report.get("result") or {}
    print(report.get("message", ""))

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload.get("markdown", ""), encoding="utf-8")
        print(f"markdown written: {out_path}")

    if not args.quiet:
        print()
        print(payload.get("discord", ""))

    if args.channel:
        if payload["totals"]["commits"] == 0:
            print("no commits in window; nothing posted to Discord")
            return 0
        delivery = post_to_discord(payload.get("discord", ""), args.channel,
                                   token=load_token())
        if delivery.get("success"):
            print(f"posted to Discord channel {args.channel} (message {delivery['messageId']})")
        else:
            # A failed post must not fail the whole run: the report itself succeeded.
            print(f"Discord delivery failed: {delivery.get('error')} "
                  f"{delivery.get('detail', '')}".strip(), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
