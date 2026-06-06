"""CLI entry for scheduled GitHub fleet morning digest."""

from __future__ import annotations

import argparse
import json
import sys

from git_github_mcp.services.morning_digest import run_morning_digest


def main() -> int:
    parser = argparse.ArgumentParser(description="GitHub fleet morning digest (breakfast runner)")
    parser.add_argument("--fleet-file", help="Path to owner/repo list file")
    parser.add_argument("--stale-days", type=int, default=7)
    parser.add_argument("--no-issues", action="store_true")
    parser.add_argument("--no-notifications", action="store_true")
    parser.add_argument("--limit", type=int, default=30, dest="limit_per_repo")
    parser.add_argument("--maintainer", dest="maintainer_login")
    parser.add_argument("--deliver", help="Comma-separated: file,aiwatcher,robofang")
    parser.add_argument("--output", dest="output_file")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of markdown")
    parser.add_argument("--all-notifications", action="store_true", help="Ignore last-run filter")
    args = parser.parse_args()

    result = run_morning_digest(
        fleet_repos_file=args.fleet_file,
        stale_days=args.stale_days,
        include_issues=not args.no_issues,
        include_notifications=not args.no_notifications,
        limit_per_repo=args.limit_per_repo,
        maintainer_login=args.maintainer_login,
        deliver=args.deliver,
        output_file=args.output_file,
        since_last_run=not args.all_notifications,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    elif result.get("success"):
        payload = result.get("result") or {}
        print(payload.get("markdown") or json.dumps(payload, indent=2))
    else:
        print(result.get("error") or "digest failed", file=sys.stderr)
        return 1

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
