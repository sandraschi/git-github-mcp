"""Fleet integrations — scraper grades, gitingest bundle."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from typing import Any

from ..utils.gitingest_urls import build_gitingest_url
from ..utils.response import success_response
from .fleet_common import DEFAULT_FLEET_OWNER, get_json
from .fleet_health import _resolve_repos

logger = logging.getLogger("git-github-mcp.fleet_links")

_SCRAPER_DIR = os.getenv("SCRAPER_MCP_DIR", "D:/Dev/repos/scraper-mcp")
_SCRAPER_PORT = 10998


def _ensure_scraper_running() -> bool:
    """Start scraper-mcp if not already listening on port 10998."""
    base = os.getenv("SCRAPER_MCP_URL", f"http://127.0.0.1:{_SCRAPER_PORT}")
    ok, _, _ = get_json(f"{base}/health", timeout=2.0)
    if ok:
        return True
    if not os.path.isdir(_SCRAPER_DIR):
        logger.warning("scraper-mcp dir not found at %s", _SCRAPER_DIR)
        return False
    logger.info("Starting scraper-mcp from %s", _SCRAPER_DIR)
    try:
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "scraper_mcp.server:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(_SCRAPER_PORT),
            ],
            cwd=_SCRAPER_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(10):
            time.sleep(1.5)
            ok, _, _ = get_json(f"{base}/health", timeout=2.0)
            if ok:
                logger.info("scraper-mcp started (pid %d)", proc.pid)
                return True
        logger.warning("scraper-mcp failed to become healthy within 15s")
        proc.kill()
    except Exception as e:
        logger.warning("Failed to start scraper-mcp: %s", e)
    return False


def op_grade_snapshot(
    *,
    owner: str = DEFAULT_FLEET_OWNER,
    scraper_url: str | None = None,
) -> dict[str, Any]:
    base = (scraper_url or os.getenv("SCRAPER_MCP_URL", f"http://127.0.0.1:{_SCRAPER_PORT}")).rstrip("/")
    ok, data, _ = get_json(f"{base}/api/coverage?owner={owner}")
    if not ok or not isinstance(data, dict):
        _ensure_scraper_running()
        ok, data, _ = get_json(f"{base}/api/coverage?owner={owner}")
    if ok and isinstance(data, dict):
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
    return success_response(
        {
            "ok": False,
            "scraper_url": base,
            "error": "scraper-mcp not running",
            "matrix": None,
        },
        "grade_snapshot",
        message="scraper-mcp not running — unable to auto-start",
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
