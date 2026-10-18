"""CLI entry for scheduled GitHub fleet weekly hygiene suite (full_suite)."""

from __future__ import annotations

import argparse
import json
import sys

from git_github_mcp.services.fleet_orchestrator import run_full_suite

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="GitHub fleet weekly suite (hygiene automation)")
    parser.add_argument("--fleet-file", help="Path to owner/repo list file")
    parser.add_argument("--stale-days", type=int, default=7)
    parser.add_argument("--deliver", default="file,aiwatcher", help="Comma-separated: file,aiwatcher,robofang")
    parser.add_argument("--maintainer", dest="maintainer_login")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of summary")
    args = parser.parse_args()

    result = run_full_suite(
        fleet_repos_file=args.fleet_file,
        stale_days=args.stale_days,
        deliver=args.deliver,
        maintainer_login=args.maintainer_login,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    elif result.get("success"):
        print("weekly-suite ok")
    else:
        print(result.get("error") or "weekly suite failed", file=sys.stderr)
        return 1

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
