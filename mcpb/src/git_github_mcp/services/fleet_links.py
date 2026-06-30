"""Fleet integrations — scraper grades, gitingest bundle."""

from __future__ import annotations

import os
from typing import Any

from ..utils.gitingest_urls import build_gitingest_url
from ..utils.response import success_response
from .fleet_common import DEFAULT_FLEET_OWNER, get_json
from .fleet_health import _resolve_repos


def op_grade_snapshot(
    *,
    owner: str = DEFAULT_FLEET_OWNER,
    scraper_url: str | None = None,
) -> dict[str, Any]:
    base = (scraper_url or os.getenv("SCRAPER_MCP_URL", "http://127.0.0.1:10998")).rstrip("/")
    ok, data, err = get_json(f"{base}/api/coverage?owner={owner}")
    if not ok or not isinstance(data, dict):
        return success_response(
            {
                "ok": False,
                "scraper_url": base,
                "error": err or "scraper-mcp unreachable",
                "matrix": None,
            },
            "grade_snapshot",
            message="scraper-mcp offline — start scraper-mcp on 10998",
        )
    return success_response(
        {
            "ok": True,
            "scraper_url": base,
            "matrix": data,
            "repo_count": data.get("repo_count"),
            "platforms": data.get("platforms"),
        },
        "grade_snapshot",
        message=f"Grade matrix for {owner} from scraper-mcp",
    )


def op_gitingest_bundle(
    *,
    fleet_repos: str | None = None,
    fleet_repos_file: str | None = None,
    use_registry: bool = True,
    ref: str | None = None,
) -> dict[str, Any]:
    repos = _resolve_repos(fleet_repos=fleet_repos, fleet_repos_file=fleet_repos_file, use_registry=use_registry)
    links: list[dict[str, str]] = []
    for owner, repo in repos:
        url = build_gitingest_url(owner, repo, ref=ref)
        links.append(
            {
                "repo_slug": f"{owner}/{repo}",
                "github_url": f"https://github.com/{owner}/{repo}",
                "gitingest_url": url,
            }
        )
    return success_response(
        {"count": len(links), "links": links},
        "gitingest_bundle",
        message=f"{len(links)} gitingest URLs for fleet repos",
    )
