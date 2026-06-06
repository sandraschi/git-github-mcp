"""Fleet workspace — local git dirty state, release version drift."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..tools.github_ops import github_ops
from ..utils.response import success_response
from .fleet_catalog import load_registry
from .fleet_common import DEFAULT_REGISTRY_PATH, DEFAULT_REPOS_ROOT, read_pyproject_version, run_git
from .fleet_health import _resolve_repos


def op_local_dirty(
    *,
    registry_path: str | None = None,
    repos_root: str | None = None,
    fleet_repos: str | None = None,
    use_registry: bool = True,
) -> dict[str, Any]:
    entries = load_registry(Path(registry_path) if registry_path else DEFAULT_REGISTRY_PATH)
    root = Path(repos_root) if repos_root else DEFAULT_REPOS_ROOT
    by_id = {str(r.get("id")): r for r in entries if isinstance(r, dict) and r.get("id")}

    if use_registry and entries:
        targets = [
            (str(r.get("id")), Path(str(r.get("repo_path") or root / str(r.get("id")))))
            for r in entries
            if isinstance(r, dict) and str(r.get("status") or "active").lower() not in ("quarantined",)
        ]
    else:
        from .fleet_common import load_fleet_repos

        repos = load_fleet_repos(fleet_repos=fleet_repos)
        targets = [(repo, root / repo) for _, repo in repos]

    dirty: list[dict[str, Any]] = []
    ahead: list[dict[str, Any]] = []
    missing: list[str] = []

    for rid, repo_path in targets:
        if not repo_path.is_dir():
            missing.append(str(repo_path))
            continue
        ok, status_out, _ = run_git(["status", "--porcelain"], repo_path)
        if not ok:
            continue
        lines = [ln for ln in status_out.splitlines() if ln.strip()]
        if lines:
            dirty.append(
                {
                    "id": rid,
                    "repo_path": str(repo_path),
                    "changed_files": len(lines),
                    "sample": lines[:8],
                }
            )
        ok2, ahead_out, _ = run_git(["rev-list", "--left-right", "--count", "HEAD...@{u}"], repo_path)
        if ok2 and ahead_out.strip():
            parts = ahead_out.strip().split()
            if len(parts) == 2:
                behind, infront = int(parts[0]), int(parts[1])
                if infront > 0 or behind > 0:
                    entry = by_id.get(rid) or {}
                    ahead.append(
                        {
                            "id": rid,
                            "repo_path": str(repo_path),
                            "ahead": infront,
                            "behind": behind,
                            "slug": entry.get("id"),
                        }
                    )

    return success_response(
        {
            "dirty_count": len(dirty),
            "sync_drift_count": len(ahead),
            "missing_paths": missing,
            "dirty": dirty,
            "sync_drift": ahead,
        },
        "local_dirty",
        message=f"{len(dirty)} dirty worktrees, {len(ahead)} ahead/behind origin",
    )


def op_release_drift(
    *,
    fleet_repos: str | None = None,
    fleet_repos_file: str | None = None,
    use_registry: bool = True,
    repos_root: str | None = None,
) -> dict[str, Any]:
    repos = _resolve_repos(
        fleet_repos=fleet_repos, fleet_repos_file=fleet_repos_file, use_registry=use_registry
    )
    root = Path(repos_root) if repos_root else DEFAULT_REPOS_ROOT
    entries = load_registry()
    path_by_id = {
        str(r.get("id")): Path(str(r.get("repo_path") or root / str(r.get("id"))))
        for r in entries
        if isinstance(r, dict)
    }

    drifts: list[dict[str, Any]] = []
    for owner, repo in repos:
        slug = f"{owner}/{repo}"
        local_path = path_by_id.get(repo, root / repo)
        local_ver = read_pyproject_version(local_path) if local_path.is_dir() else None
        res = github_ops(operation="release_list", owner=owner, repo=repo, limit=3)
        latest_tag = None
        if res.get("success"):
            releases = (res.get("result") or {}).get("releases") or []
            if releases and isinstance(releases[0], dict):
                latest_tag = releases[0].get("tagName")
        if local_ver and latest_tag and local_ver != latest_tag.replace("v", "").replace("V", ""):
            drifts.append(
                {
                    "repo_slug": slug,
                    "repo_url": f"https://github.com/{slug}",
                    "local_version": local_ver,
                    "latest_release_tag": latest_tag,
                    "repo_path": str(local_path),
                }
            )
        elif local_ver and not latest_tag:
            drifts.append(
                {
                    "repo_slug": slug,
                    "repo_url": f"https://github.com/{slug}",
                    "local_version": local_ver,
                    "latest_release_tag": None,
                    "note": "no GitHub release found",
                    "repo_path": str(local_path),
                }
            )

    return success_response(
        {"drift_count": len(drifts), "drifts": drifts},
        "release_drift",
        message=f"{len(drifts)} repos with local/release version skew",
    )
