"""GitHub operations portmanteau via gh CLI.

Requires: gh auth login (https://cli.github.com)
"""

import json
from typing import Any

from ..utils.gh_cli import run_gh
from ..utils.github_format import (
    build_code_find_query,
    build_topic_repo_query,
    format_code_search_markdown,
    format_repo_card,
)
from ..utils.gitingest_urls import (
    GITINGEST_HELP_MARKDOWN,
    build_gitingest_url,
    github_url_to_gitingest,
)
from ..utils.response import error_response, success_response

ACTION_TYPE = (
    # Repos
    "repo_list",
    "repo_view",
    "repo_create",
    "repo_fork",
    "repo_clone",
    "repo_delete",
    "repo_rename",
    "repo_archive",
    # Issues
    "issue_list",
    "issue_view",
    "issue_create",
    "issue_close",
    "issue_comment",
    # PRs
    "pr_list",
    "pr_view",
    "pr_create",
    "pr_merge",
    "pr_checkout",
    "pr_close",
    "pr_comment",
    # Releases
    "release_list",
    "release_view",
    "release_create",
    "release_delete",
    "release_update",
    # Workflows (Actions)
    "workflow_list",
    "workflow_run",
    "workflow_runs",
    "workflow_view",
    "workflow_rerun",
    "workflow_cancel",
    "workflow_disable",
    "workflow_enable",
    # Labels
    "label_list",
    "label_create",
    "label_delete",
    # Secrets
    "secrets_list",
    "secrets_set",
    "secrets_delete",
    # Collaborators
    "collaborator_add",
    "collaborator_remove",
    # Search
    "search_repos",
    "search_issues",
    "search_code",
    "search_repos_topic",
    "search_repos_by_topic",
    "user_repos_full",
    "code_find_repos",
    # Stars analytics (received)
    "stars_summary",
    "stars_per_repo",
    "stars_history",
    # Repo display
    "show_repo",
    # GitHub Projects (classic / Projects v2 via gh project)
    "project_list",
    "project_view",
    "project_create",
    "project_delete",
    "project_edit",
    # GitHub Packages (REST via gh api)
    "package_list",
    "package_view",
    "package_delete",
    # Gitingest (LLM-friendly repo digest URLs — https://gitingest.com)
    "gitingest_link",
    "gitingest_convert_url",
    "gitingest_help",
    # Auth / misc
    "auth_status",
    "gist_list",
)


def _j(s: str) -> Any:
    """Parse JSON safely."""
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return []


def _pr_comment_count(raw: Any) -> int:
    """gh pr list --json comments returns a list of comment objects (not a count)."""
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


def _normalize_pr_row(row: dict[str, Any]) -> dict[str, Any]:
    if "comments" in row:
        row = {**row, "comments": _pr_comment_count(row.get("comments"))}
    return row


def _ok(op: str, data: dict, message: str | None = None, next_steps: list | None = None) -> dict:
    return success_response(data, op, message=message, next_steps=next_steps or [])


def _err(op: str, msg: str, **kw) -> dict:
    return error_response(op, msg, **kw)


def _repo_arg(owner: str | None, repo: str | None) -> str | None:
    if owner and repo:
        return f"{owner}/{repo}"
    return None


def github_ops(
    operation: str,
    # Repo identifiers
    owner: str | None = None,
    repo: str | None = None,
    # Issue / PR fields
    title: str | None = None,
    body: str | None = None,
    issue_number: int | None = None,
    pr_number: int | None = None,
    # Lists / filters
    state: str = "open",
    limit: int = 20,
    label: str | None = None,
    assignee: str | None = None,
    # Repo create / rename
    description: str | None = None,
    private: bool = False,
    new_name: str | None = None,
    # PR
    base_branch: str | None = None,
    head_branch: str | None = None,
    draft: bool = False,
    merge_method: str = "merge",  # merge | squash | rebase
    # Release
    tag_name: str | None = None,
    release_name: str | None = None,
    prerelease: bool = False,
    # Search
    query: str | None = None,
    # Workflow
    workflow_id: str | None = None,
    run_id: str | None = None,
    failed_job_id: str | None = None,
    ref: str | None = None,
    # Clone target
    target_dir: str | None = None,
    # Secrets
    secret_name: str | None = None,
    secret_value: str | None = None,
    # Collaborators
    username: str | None = None,
    permission: str = "push",  # pull | push | admin | maintain | triage
    # Labels
    label_name: str | None = None,
    label_color: str | None = None,
    label_description: str | None = None,
    # Pretty repo card (show_repo): markdown | html | json
    output_format: str = "markdown",
    # Repository topic / code discovery (GitHub repo "topics" = tags)
    topic: str | None = None,
    extension: str | None = None,
    path_pattern: str | None = None,
    search_scope: str | None = None,
    # If True with search_code: add markdown table + unique_repositories
    pretty: bool = False,
    # For user_repos_full: filter by visibility
    visibility: str = "",  # "public", "private", "internal", or "" for all
    # GitHub Projects (gh project — may need: gh auth refresh -s project)
    project_number: int | None = None,
    # GitHub Packages (gh api — scope read:packages / write:packages)
    package_type: str | None = None,
    package_name: str | None = None,
    # Gitingest: optional subpath under ref; full GitHub URL for convert
    subpath: str | None = None,
    github_url: str | None = None,
) -> dict[str, Any]:
    """GitHub operations via gh CLI — 61 actions.

    REPOS:         repo_list, repo_view, show_repo, repo_create, repo_fork, repo_clone,
                   repo_delete, repo_rename, repo_archive
    ISSUES:        issue_list, issue_view, issue_create, issue_close, issue_comment
    PRs:           pr_list, pr_view, pr_create, pr_merge, pr_checkout, pr_close, pr_comment
    RELEASES:      release_list, release_view, release_create, release_delete, release_update
    ACTIONS:       workflow_list, workflow_run, workflow_runs,
                   workflow_cancel, workflow_disable, workflow_enable
    LABELS:        label_list, label_create, label_delete
    SECRETS:       secrets_list, secrets_set, secrets_delete
    COLLABORATORS: collaborator_add, collaborator_remove
    SEARCH:        search_repos, search_repos_topic, search_repos_by_topic, search_issues,
                   search_code (pretty=), code_find_repos
    FLEET AUDIT:   user_repos_full
    STARS:         stars_summary, stars_per_repo, stars_history
    PROJECTS:      project_list, project_view, project_create, project_delete, project_edit
    PACKAGES:      package_list, package_view, package_delete
    GITINGEST:     gitingest_link, gitingest_convert_url, gitingest_help
    MISC:          auth_status, gist_list

    Requires gh CLI: https://cli.github.com — run 'gh auth login' first.
    """
    if operation not in ACTION_TYPE:
        return _err(operation, f"Unknown operation. Valid: {', '.join(sorted(ACTION_TYPE))}")

    slug = _repo_arg(owner, repo)

    # ── Auth / misc ───────────────────────────────────────────────────────────
    if operation == "auth_status":
        ok, out, err = run_gh(["auth", "status"])
        return _ok("auth_status", {"output": (out + err).strip(), "authenticated": ok})

    if operation == "gist_list":
        ok, out, err = run_gh(["gist", "list", "--limit", str(limit), "--json", "id,description,public,updatedAt"])
        if not ok:
            return _err("gist_list", err or "gist list failed")
        return _ok("gist_list", {"gists": _j(out), "count": len(_j(out))})

    # ── Repos ─────────────────────────────────────────────────────────────────
    if operation == "repo_list":
        args = [
            "repo",
            "list",
            "--limit",
            str(limit),
            "--json",
            "name,description,isPrivate,stargazerCount,updatedAt,url,defaultBranchRef",
        ]
        if owner:
            args.insert(2, owner)
        ok, out, err = run_gh(args)
        if not ok:
            return _err("repo_list", err or "repo list failed")
        data = _j(out)
        return _ok(
            "repo_list",
            {"repos": data, "count": len(data)},
            next_steps=["github_ops(operation='repo_view', owner='...', repo='...')"],
        )

    if operation == "user_repos_full":
        if not owner:
            return _err("user_repos_full", "owner required")
        per_page = 100
        page = 1
        all_repos: list[dict] = []
        while True:
            path = f"users/{owner}/repos?per_page={per_page}&page={page}&sort=pushed&direction=desc"
            if visibility:
                path += f"&type={visibility}"
            ok, out, err = run_gh(["api", "--paginate", path], timeout=120)
            if not ok:
                return _err("user_repos_full", err or "API call failed")
            data = _j(out)
            if not isinstance(data, list):
                break
            all_repos.extend(data)
            if len(data) < per_page:
                break
            page += 1
        return _ok(
            "user_repos_full",
            {"repos": all_repos, "count": len(all_repos), "owner": owner, "visibility": visibility or "all"},
            message=f"All {len(all_repos)} repos for {owner} — full metadata",
            next_steps=[f"github_ops(operation='search_repos_by_topic', topic='mcp', owner='{owner}')"],
        )

    # ── Stars analytics (received) ────────────────────────────────────────────
    if operation == "stars_summary":
        target_owner = owner
        if not target_owner:
            ok_u, out_u, _ = run_gh(["api", "user", "--jq", ".login"])
            if ok_u and out_u.strip():
                target_owner = out_u.strip().strip('"')
            else:
                return _err("stars_summary", "owner required (or run gh auth login to infer)")
        per_page = 100
        page = 1
        all_repos: list[dict] = []
        while True:
            path = f"users/{target_owner}/repos?per_page={per_page}&page={page}&sort=updated&direction=desc"
            # visibility filter for stars_summary mirrors user_repos_full type param
            if visibility:
                path += f"&type={visibility}"
            ok, out, err = run_gh(["api", path], timeout=60)
            if not ok:
                # unauthenticated fallback via REST paginate error - try repo list as fallback
                if "401" in (err or "") or "Requires authentication" in (err or ""):
                    ok2, out2, err2 = run_gh(
                        [
                            "repo",
                            "list",
                            target_owner,
                            "--limit",
                            "1000",
                            "--json",
                            "name,description,isPrivate,stargazerCount,forkCount,updatedAt,url",
                        ],
                        timeout=60,
                    )
                    if ok2:
                        data2 = _j(out2)
                        if isinstance(data2, list):
                            # normalize to REST shape stargazers_count
                            for r in data2:
                                if "stargazerCount" in r and "stargazers_count" not in r:
                                    r["stargazers_count"] = r.pop("stargazerCount")
                                if "forkCount" in r and "forks_count" not in r:
                                    r["forks_count"] = r.pop("forkCount")
                            all_repos = data2
                            break
                    return _err(
                        "stars_summary", err or err2 or "API call failed — gh auth login required for full list"
                    )
                return _err("stars_summary", err or "API call failed")
            data = _j(out)
            if not isinstance(data, list):
                break
            all_repos.extend(data)
            if len(data) < per_page:
                break
            page += 1
            if page > 10:  # safety cap 1000 repos
                break

        # compute aggregates
        def _stars(r: dict) -> int:
            return int(r.get("stargazers_count", r.get("stargazerCount", 0)) or 0)

        def _forks(r: dict) -> int:
            return int(r.get("forks_count", r.get("forkCount", 0)) or 0)

        total_stars = sum(_stars(r) for r in all_repos)
        total_forks = sum(_forks(r) for r in all_repos)
        total_repos = len(all_repos)
        avg_stars = round(total_stars / total_repos, 2) if total_repos else 0
        sorted_repos = sorted(all_repos, key=_stars, reverse=True)
        # median
        stars_sorted = sorted(_stars(r) for r in all_repos)
        median_stars = 0
        if stars_sorted:
            mid = len(stars_sorted) // 2
            if len(stars_sorted) % 2 == 0:
                median_stars = (stars_sorted[mid - 1] + stars_sorted[mid]) / 2
            else:
                median_stars = float(stars_sorted[mid])
        zero = sum(1 for r in all_repos if _stars(r) == 0)
        # distribution buckets
        buckets = {"0": 0, "1-4": 0, "5-19": 0, "20-49": 0, "50-99": 0, "100+": 0}
        for r in all_repos:
            s = _stars(r)
            if s == 0:
                buckets["0"] += 1
            elif 1 <= s <= 4:
                buckets["1-4"] += 1
            elif 5 <= s <= 19:
                buckets["5-19"] += 1
            elif 20 <= s <= 49:
                buckets["20-49"] += 1
            elif 50 <= s <= 99:
                buckets["50-99"] += 1
            else:
                buckets["100+"] += 1
        top_n = max(1, min(int(limit) if limit else 30, 100))
        top_repos = []
        for r in sorted_repos[:top_n]:
            top_repos.append(
                {
                    "name": r.get("name"),
                    "description": r.get("description"),
                    "isPrivate": r.get("private", r.get("isPrivate", False)),
                    "stargazerCount": _stars(r),
                    "forkCount": _forks(r),
                    "updatedAt": r.get("updated_at", r.get("updatedAt")),
                    "pushedAt": r.get("pushed_at", r.get("pushedAt")),
                    "url": r.get("html_url", r.get("url")),
                    "language": r.get("language"),
                }
            )
        return _ok(
            "stars_summary",
            {
                "owner": target_owner,
                "total_repos": total_repos,
                "total_stars": total_stars,
                "total_forks": total_forks,
                "avg_stars": avg_stars,
                "median_stars": median_stars,
                "zero_star_repos": zero,
                "distribution": buckets,
                "top_repos": top_repos,
                "visibility": visibility or "all",
                "fetched_at": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat()
                if hasattr(__import__("datetime").datetime, "UTC")
                else __import__("datetime").datetime.utcnow().isoformat() + "Z",
            },
            message=f"Total {total_stars} stars across {total_repos} repos for {target_owner} (avg {avg_stars}, median {median_stars})",
            next_steps=["github_ops(operation='stars_per_repo', owner='...', repo='...')"],
        )

    if operation == "stars_per_repo":
        if not slug:
            return _err("stars_per_repo", "owner and repo required")
        ok, out, err = run_gh(
            [
                "api",
                f"repos/{slug}",
                "--jq",
                "{name:.name, description:.description, isPrivate:.private, stargazerCount:.stargazers_count, forkCount:.forks_count, watchers:.watchers_count, openIssues:.open_issues_count, updatedAt:.updated_at, pushedAt:.pushed_at, language:.language, url:.html_url, private:.private}",
            ],
            timeout=30,
        )
        if not ok:
            # fallback to repo view
            ok2, out2, err2 = run_gh(
                ["repo", "view", slug, "--json", "name,description,isPrivate,stargazerCount,forkCount,updatedAt,url"],
                timeout=30,
            )
            if not ok2:
                return _err("stars_per_repo", err or err2 or "repo view failed")
            data2 = _j(out2)
            if isinstance(data2, dict):
                data2 = {
                    **data2,
                    "stargazerCount": data2.get("stargazerCount", 0),
                    "forkCount": data2.get("forkCount", 0),
                }
                return _ok(
                    "stars_per_repo",
                    {"repository": slug, **data2},
                    message=f"{slug} has {data2.get('stargazerCount', 0)} stars",
                )
            return _err("stars_per_repo", "unexpected gh output")
        data = _j(out)
        if isinstance(data, dict):
            return _ok(
                "stars_per_repo",
                {"repository": slug, **data},
                message=f"{slug} has {data.get('stargazerCount', 0)} stars",
            )
        # out was raw jq string - parse
        try:
            data = json.loads(out) if out.strip().startswith("{") else {}
        except Exception:
            data = {}
        return _ok("stars_per_repo", {"repository": slug, **data})

    if operation == "stars_history":
        # trajectory: bucketed cumulative stars over time
        # params: owner, repo (optional), limit (top N repos if owner only), bucket (month/week)
        target_owner = owner
        if not target_owner:
            ok_u, out_u, _ = run_gh(["api", "user", "--jq", ".login"])
            if ok_u and out_u.strip():
                target_owner = out_u.strip().strip('"')
            else:
                return _err("stars_history", "owner required (or gh auth login)")
        # bucket param via label field to avoid adding new param: allow bucket in query
        # prefer explicit: use query as bucket if provided
        bucket_mode = (query or "month").lower() if query else "month"
        if bucket_mode not in ("day", "week", "month"):
            bucket_mode = "month"
        repos_to_scan: list[str] = []
        if repo:
            if not target_owner:
                return _err("stars_history", "owner required with repo")
            repos_to_scan = [f"{target_owner}/{repo}"]
        else:
            # need top repos to scan - reuse stars_summary logic fast path: gh repo list
            ok_l, out_l, _ = run_gh(
                ["repo", "list", target_owner, "--limit", str(min(int(limit) if limit else 30, 80)), "--json", "name"],
                timeout=60,
            )
            if ok_l:
                data_l = _j(out_l)
                if isinstance(data_l, list):
                    repos_to_scan = [f"{target_owner}/{r.get('name')}" for r in data_l if r.get("name")]
            if not repos_to_scan:
                # fallback: try single repo list via API pagination
                ok_l2, out_l2, _ = run_gh(["api", f"users/{target_owner}/repos?per_page=30&sort=updated"], timeout=60)
                if ok_l2:
                    data_l2 = _j(out_l2)
                    if isinstance(data_l2, list):
                        repos_to_scan = [f"{target_owner}/{r.get('name')}" for r in data_l2[:20] if r.get("name")]
        if not repos_to_scan:
            return _err("stars_history", "no repos found to scan")
        # fetch stargazers for each repo
        from datetime import datetime

        def _bucket_key(dt: datetime, mode: str) -> str:
            if mode == "day":
                return dt.strftime("%Y-%m-%d")
            if mode == "week":
                # ISO week
                y, w, _ = dt.isocalendar()
                return f"{y}-W{w:02d}"
            return dt.strftime("%Y-%m")

        all_dates: list[datetime] = []
        per_repo_points: dict[str, list[str]] = {}
        failed: list[str] = []
        for slug_scan in repos_to_scan:
            ok_s, out_s, _err_s = run_gh(
                ["api", f"repos/{slug_scan}/stargazers?per_page=100", "--paginate", "--jq", ".[].starred_at // empty"],
                timeout=90,
            )
            if not ok_s:
                # 401 -> need auth for starred_at (requires star+json media)
                # try with header via gh api -H
                ok_s2, out_s2, _ = run_gh(
                    [
                        "api",
                        f"repos/{slug_scan}/stargazers",
                        "-H",
                        "Accept: application/vnd.github.star+json",
                        "--paginate",
                        "--jq",
                        ".[].starred_at // .[].starred_at // empty",
                    ],
                    timeout=90,
                )
                if not ok_s2:
                    # fallback: no history, just use current count at today
                    failed.append(slug_scan)
                    continue
                out_s = out_s2
            dates_raw = [d.strip().strip('"') for d in out_s.splitlines() if d.strip()]
            per_repo_points[slug_scan] = dates_raw
            for ds in dates_raw:
                try:
                    # GitHub returns ISO8601 like 2026-09-03T17:50:03Z
                    dt = datetime.fromisoformat(ds.replace("Z", "+00:00"))
                    all_dates.append(dt)
                except Exception:
                    continue
        if not all_dates and failed:
            return _ok(
                "stars_history",
                {
                    "owner": target_owner,
                    "repo": repo or None,
                    "bucket": bucket_mode,
                    "points": [],
                    "per_repo": per_repo_points,
                    "note": "stargazers history requires gh auth (star+json). Run gh auth login with repo scope or add --jq starred_at fallback. Showing empty until authed.",
                    "failed_repos": failed,
                },
                message="No stargazer timestamps available without auth; run gh auth login",
            )
        # bucket counts
        from collections import Counter

        bucket_counts: Counter = Counter()
        for dt in all_dates:
            bucket_counts[_bucket_key(dt, bucket_mode)] += 1
        # sort buckets chronologically
        sorted_keys = sorted(bucket_counts.keys())
        # cumulative
        cumulative = 0
        points: list[dict] = []
        for k in sorted_keys:
            cumulative += bucket_counts[k]
            points.append({"bucket": k, "new": bucket_counts[k], "cumulative": cumulative})
        # also build monthly total across all repos if trajectory for owner
        payload: dict = {
            "owner": target_owner,
            "repo": repo or None,
            "bucket": bucket_mode,
            "points": points,
            "per_repo": {k: len(v) for k, v in per_repo_points.items()},
            "total_events": len(all_dates),
            "failed_repos": failed,
            "repos_scanned": len(repos_to_scan),
        }
        if not points:
            payload["note"] = (
                "No stargazer timestamps — gh auth required (Accept: star+json). Run gh auth login then retry for history."
            )
        return _ok(
            "stars_history",
            payload,
            message=f"Star trajectory for {repo or target_owner}: {len(all_dates)} events across {len(repos_to_scan)} repos ({bucket_mode})",
        )

    if operation == "repo_view":
        if not slug:
            return _err("repo_view", "owner and repo required")
        ok, out, err = run_gh(
            [
                "repo",
                "view",
                slug,
                "--json",
                "name,description,isPrivate,stargazerCount,forkCount,"
                "issues,url,sshUrl,defaultBranchRef,languages,repositoryTopics",
            ]
        )
        if not ok:
            return _err("repo_view", err or "repo view failed")
        return _ok("repo_view", _j(out) if isinstance(_j(out), dict) else {"raw": out.strip()})

    if operation == "show_repo":
        if not slug:
            return _err("show_repo", "owner and repo required")
        ok, out, err = run_gh(
            [
                "repo",
                "view",
                slug,
                "--json",
                "name,description,isPrivate,stargazerCount,forkCount,"
                "issues,url,sshUrl,defaultBranchRef,languages,repositoryTopics",
            ]
        )
        if not ok:
            return _err("show_repo", err or "repo view failed")
        raw = _j(out)
        if not isinstance(raw, dict):
            return _err("show_repo", "unexpected gh output")
        fmt = (output_format or "markdown").strip().lower()
        card = format_repo_card(raw, fmt)
        payload: dict[str, Any] = {
            "format": fmt,
            "content": card,
            "repository": slug,
            "raw": raw,
        }
        return _ok(
            "show_repo",
            payload,
            message="Repository card — use `content` in Markdown/HTML preview",
            next_steps=[f"github_ops(operation='repo_clone', owner='{owner}', repo='{repo}')"],
        )

    if operation == "repo_create":
        if not repo:
            return _err("repo_create", "repo (name) required")
        args = ["repo", "create", repo, "--confirm"]
        if description:
            args += ["--description", description]
        args.append("--private" if private else "--public")
        ok, out, err = run_gh(args)
        if not ok:
            return _err(
                "repo_create",
                err or "repo create failed",
                recovery_options=["Check gh auth", "Name may be taken"],
            )
        return _ok("repo_create", {"url": out.strip()}, message="Repository created")

    if operation == "repo_fork":
        if not slug:
            return _err("repo_fork", "owner and repo required")
        args = ["repo", "fork", slug, "--clone=false"]
        ok, out, err = run_gh(args)
        if not ok:
            return _err("repo_fork", err or "fork failed")
        return _ok("repo_fork", {"output": (out + err).strip()}, message="Forked")

    if operation == "repo_clone":
        if not slug:
            return _err("repo_clone", "owner and repo required")
        args = ["repo", "clone", slug]
        if target_dir:
            args.append(target_dir)
        ok, out, err = run_gh(args, timeout=120)
        if not ok:
            return _err("repo_clone", err or "clone failed")
        return _ok("repo_clone", {"output": (out + err).strip()})

    if operation == "repo_delete":
        if not slug:
            return _err("repo_delete", "owner and repo required")
        ok, out, err = run_gh(["repo", "delete", slug, "--yes"])
        if not ok:
            return _err(
                "repo_delete",
                err or "repo delete failed",
                recovery_options=["Check gh auth", "Requires admin access"],
            )
        return _ok("repo_delete", {"repo": slug}, message=f"Repository {slug} deleted")

    if operation == "repo_rename":
        if not slug:
            return _err("repo_rename", "owner and repo required")
        if not new_name:
            return _err("repo_rename", "new_name required")
        ok, out, err = run_gh(["repo", "rename", new_name, "--repo", slug, "--yes"])
        if not ok:
            return _err("repo_rename", err or "repo rename failed")
        return _ok(
            "repo_rename",
            {"old_name": repo, "new_name": new_name, "output": out.strip()},
            message=f"Repository renamed to {new_name}",
        )

    if operation == "repo_archive":
        if not slug:
            return _err("repo_archive", "owner and repo required")
        ok, out, err = run_gh(["repo", "archive", slug, "--yes"])
        if not ok:
            return _err("repo_archive", err or "repo archive failed")
        return _ok("repo_archive", {"repo": slug}, message=f"Repository {slug} archived")

    if operation == "user_repos_full":
        args = [
            "repo",
            "list",
            "--limit",
            str(max(1, min(int(limit), 1000))),
            "--json",
            (
                "name,description,isPrivate,isFork,isArchived,isTemplate,"
                "stargazerCount,forkCount,watchers,updatedAt,pushedAt,"
                "url,sshUrl,primaryLanguage,languages,repositoryTopics,defaultBranchRef"
            ),
        ]
        if owner:
            args.insert(2, owner)
        ok, out, err = run_gh(args)
        if not ok:
            return _err("user_repos_full", err or "repo list failed")
        data = _j(out)
        if not isinstance(data, list):
            data = []
        # Build summary statistics
        total = len(data)
        public_count = sum(1 for r in data if not r.get("isPrivate", False))
        private_count = total - public_count
        archived_count = sum(1 for r in data if r.get("isArchived", False))
        fork_count = sum(1 for r in data if r.get("isFork", False))
        template_count = sum(1 for r in data if r.get("isTemplate", False))
        source_count = total - fork_count
        return _ok(
            "user_repos_full",
            {
                "repos": data,
                "summary": {
                    "total": total,
                    "public": public_count,
                    "private": private_count,
                    "archived": archived_count,
                    "forks": fork_count,
                    "templates": template_count,
                    "source_repos": source_count,
                },
                "owner": owner or "@me",
            },
            message=(
                f"{total} repos ({public_count} public, {private_count} private, "
                f"{archived_count} archived, {fork_count} forks)"
            ),
            next_steps=[
                f"github_ops(operation='show_repo', owner='{owner or 'YOU'}', repo='REPO_NAME')",
                ("github_ops(operation='user_repos_full', owner='YOU', limit=200) for larger lists"),
            ],
        )

    # ── Issues ────────────────────────────────────────────────────────────────
    if operation == "issue_list":
        if not slug:
            return _err("issue_list", "owner and repo required")
        args = [
            "issue",
            "list",
            "--repo",
            slug,
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number,title,state,url,author,labels,assignees,createdAt,updatedAt",
        ]
        if label:
            args += ["--label", label]
        if assignee:
            args += ["--assignee", assignee]
        ok, out, err = run_gh(args)
        if not ok:
            return _err("issue_list", err or "issue list failed")
        data = _j(out)
        return _ok("issue_list", {"issues": data, "count": len(data)})

    if operation == "issue_view":
        if not slug or not issue_number:
            return _err("issue_view", "owner, repo, issue_number required")
        ok, out, err = run_gh(
            [
                "issue",
                "view",
                str(issue_number),
                "--repo",
                slug,
                "--json",
                "number,title,body,state,url,author,labels,assignees,comments,createdAt,updatedAt",
            ]
        )
        if not ok:
            return _err("issue_view", err or "issue view failed")
        return _ok("issue_view", _j(out) if isinstance(_j(out), dict) else {"raw": out.strip()})

    if operation == "issue_create":
        if not slug or not title:
            return _err("issue_create", "owner, repo, title required")
        args = ["issue", "create", "--repo", slug, "--title", title]
        if body:
            args += ["--body", body]
        if label:
            args += ["--label", label]
        if assignee:
            args += ["--assignee", assignee]
        ok, out, err = run_gh(args)
        if not ok:
            return _err(
                "issue_create",
                err or "issue create failed",
                recovery_options=["gh auth login", "Check repo access"],
            )
        return _ok("issue_create", {"url": out.strip(), "title": title}, message="Issue created")

    if operation == "issue_close":
        if not slug or not issue_number:
            return _err("issue_close", "owner, repo, issue_number required")
        args = ["issue", "close", str(issue_number), "--repo", slug]
        if body:
            args += ["--comment", body]
        ok, out, err = run_gh(args)
        if not ok:
            return _err("issue_close", err or "close failed")
        return _ok("issue_close", {"issue_number": issue_number}, message="Issue closed")

    if operation == "issue_comment":
        if not slug or not issue_number or not body:
            return _err("issue_comment", "owner, repo, issue_number, body required")
        ok, out, err = run_gh(["issue", "comment", str(issue_number), "--repo", slug, "--body", body])
        if not ok:
            return _err("issue_comment", err or "comment failed")
        return _ok("issue_comment", {"url": out.strip()}, message="Comment added")

    # ── PRs ───────────────────────────────────────────────────────────────────
    if operation == "pr_list":
        if not slug:
            return _err("pr_list", "owner and repo required")
        args = [
            "pr",
            "list",
            "--repo",
            slug,
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            # comments + updatedAt help spot PRs that sat without discussion (maintainer triage)
            "number,title,state,url,author,headRefName,baseRefName,isDraft,createdAt,updatedAt,comments",
        ]
        ok, out, err = run_gh(args)
        if not ok:
            return _err("pr_list", err or "pr list failed")
        data = _j(out)
        if isinstance(data, list):
            data = [_normalize_pr_row(row) for row in data if isinstance(row, dict)]
        return _ok("pr_list", {"prs": data, "count": len(data)})

    if operation == "pr_view":
        if not slug or not pr_number:
            return _err("pr_view", "owner, repo, pr_number required")
        ok, out, err = run_gh(
            [
                "pr",
                "view",
                str(pr_number),
                "--repo",
                slug,
                "--json",
                "number,title,body,state,url,author,headRefName,"
                "baseRefName,isDraft,mergeable,comments,reviews,createdAt",
            ]
        )
        if not ok:
            return _err("pr_view", err or "pr view failed")
        return _ok("pr_view", _j(out) if isinstance(_j(out), dict) else {"raw": out.strip()})

    if operation == "pr_create":
        if not slug or not title:
            return _err("pr_create", "owner, repo, title required")
        args = ["pr", "create", "--repo", slug, "--title", title]
        if body:
            args += ["--body", body]
        if base_branch:
            args += ["--base", base_branch]
        if head_branch:
            args += ["--head", head_branch]
        if draft:
            args.append("--draft")
        ok, out, err = run_gh(args)
        if not ok:
            return _err(
                "pr_create",
                err or "pr create failed",
                recovery_options=["Push branch first", "gh auth login"],
            )
        return _ok("pr_create", {"url": out.strip(), "title": title}, message="PR created")

    if operation == "pr_merge":
        if not slug or not pr_number:
            return _err("pr_merge", "owner, repo, pr_number required")
        method_flag = {"merge": "--merge", "squash": "--squash", "rebase": "--rebase"}.get(merge_method, "--merge")
        ok, out, err = run_gh(["pr", "merge", str(pr_number), "--repo", slug, method_flag, "--auto"])
        if not ok:
            return _err("pr_merge", err or "merge failed")
        return _ok("pr_merge", {"pr_number": pr_number, "method": merge_method}, message="PR merged")

    if operation == "pr_checkout":
        if not pr_number:
            return _err("pr_checkout", "pr_number required")
        args = ["pr", "checkout", str(pr_number)]
        if slug:
            args += ["--repo", slug]
        ok, out, err = run_gh(args)
        if not ok:
            return _err("pr_checkout", err or "checkout failed")
        return _ok("pr_checkout", {"pr_number": pr_number, "output": (out + err).strip()})

    if operation == "pr_close":
        if not slug or not pr_number:
            return _err("pr_close", "owner, repo, pr_number required")
        args = ["pr", "close", str(pr_number), "--repo", slug]
        if body:
            args += ["--comment", body]
        ok, out, err = run_gh(args)
        if not ok:
            return _err("pr_close", err or "pr close failed")
        return _ok("pr_close", {"pr_number": pr_number}, message="PR closed")

    if operation == "pr_comment":
        if not slug or not pr_number or not body:
            return _err("pr_comment", "owner, repo, pr_number, body required")
        ok, out, err = run_gh(["pr", "comment", str(pr_number), "--repo", slug, "--body", body])
        if not ok:
            return _err("pr_comment", err or "pr comment failed")
        return _ok("pr_comment", {"url": out.strip()}, message="PR comment added")

    # ── Releases ──────────────────────────────────────────────────────────────
    if operation == "release_list":
        if not slug:
            return _err("release_list", "owner and repo required")
        ok, out, err = run_gh(
            [
                "release",
                "list",
                "--repo",
                slug,
                "--limit",
                str(limit),
                "--json",
                "tagName,name,isDraft,isPrerelease,isLatest,publishedAt",
            ]
        )
        if not ok:
            return _err("release_list", err or "release list failed")
        data = _j(out)
        return _ok("release_list", {"releases": data, "count": len(data)})

    if operation == "release_view":
        if not slug or not tag_name:
            return _err("release_view", "owner, repo, tag_name required")
        ok, out, err = run_gh(
            [
                "release",
                "view",
                tag_name,
                "--repo",
                slug,
                "--json",
                "tagName,name,body,isDraft,isPrerelease,publishedAt,url,assets",
            ]
        )
        if not ok:
            return _err("release_view", err or "release view failed")
        return _ok("release_view", _j(out) if isinstance(_j(out), dict) else {"raw": out.strip()})

    if operation == "release_create":
        if not slug or not tag_name:
            return _err("release_create", "owner, repo, tag_name required")
        args = ["release", "create", tag_name, "--repo", slug]
        if release_name:
            args += ["--title", release_name]
        if body:
            args += ["--notes", body]
        if prerelease:
            args.append("--prerelease")
        ok, out, err = run_gh(args)
        if not ok:
            return _err("release_create", err or "release create failed")
        return _ok("release_create", {"url": out.strip(), "tag": tag_name}, message="Release created")

    if operation == "release_delete":
        if not slug or not tag_name:
            return _err("release_delete", "owner, repo, tag_name required")
        ok, out, err = run_gh(["release", "delete", tag_name, "--repo", slug, "--yes"])
        if not ok:
            return _err("release_delete", err or "release delete failed")
        return _ok("release_delete", {"tag": tag_name}, message=f"Release {tag_name} deleted")

    if operation == "release_update":
        if not slug or not tag_name:
            return _err("release_update", "owner, repo, tag_name required")
        args = ["release", "edit", tag_name, "--repo", slug]
        if release_name:
            args += ["--title", release_name]
        if body:
            args += ["--notes", body]
        if prerelease:
            args.append("--prerelease")
        ok, out, err = run_gh(args)
        if not ok:
            return _err("release_update", err or "release update failed")
        return _ok("release_update", {"tag": tag_name, "output": out.strip()}, message="Release updated")

    # ── Workflows ─────────────────────────────────────────────────────────────
    if operation == "workflow_list":
        if not slug:
            return _err("workflow_list", "owner and repo required")
        ok, out, err = run_gh(["workflow", "list", "--repo", slug, "--json", "id,name,state"])
        if not ok:
            return _err("workflow_list", err or "workflow list failed")
        data = _j(out)
        return _ok("workflow_list", {"workflows": data, "count": len(data)})

    if operation == "workflow_run":
        if not slug or not workflow_id:
            return _err("workflow_run", "owner, repo, workflow_id required")
        args = ["workflow", "run", workflow_id, "--repo", slug]
        if ref:
            args += ["--ref", ref]
        ok, out, err = run_gh(args)
        if not ok:
            return _err("workflow_run", err or "workflow run failed")
        return _ok("workflow_run", {"output": (out + err).strip()}, message="Workflow triggered")

    if operation == "workflow_runs":
        if not slug:
            return _err("workflow_runs", "owner and repo required")
        args = [
            "run",
            "list",
            "--repo",
            slug,
            "--limit",
            str(limit),
            "--json",
            "databaseId,name,status,conclusion,headBranch,createdAt,url",
        ]
        if workflow_id:
            args += ["--workflow", workflow_id]
        ok, out, err = run_gh(args)
        if not ok:
            return _err("workflow_runs", err or "run list failed")
        data = _j(out)
        return _ok("workflow_runs", {"runs": data, "count": len(data)})

    if operation == "workflow_cancel":
        if not slug or not run_id:
            return _err("workflow_cancel", "owner, repo, run_id required")
        ok, out, err = run_gh(["run", "cancel", run_id, "--repo", slug])
        if not ok:
            return _err("workflow_cancel", err or "workflow cancel failed")
        return _ok("workflow_cancel", {"run_id": run_id}, message="Workflow run cancelled")

    if operation == "workflow_view":
        """Inspect a workflow run: jobs, per-job conclusions, and failed-step logs.

        Returns the run summary plus a 'failures' list — each entry has the
        failed job/step name, conclusion, and the tail of its log. This is
        what the web CI page and any agent need to answer "what failed?".
        """
        if not slug or not run_id:
            return _err("workflow_view", "owner, repo, run_id required")
        ok, out, err = run_gh(
            [
                "run",
                "view",
                run_id,
                "--repo",
                slug,
                "--json",
                "databaseId,name,status,conclusion,headBranch,createdAt,url,jobs",
            ],
            timeout=90,
        )
        if not ok:
            return _err("workflow_view", err or "workflow view failed")
        data = _j(out)
        jobs = (data or {}).get("jobs") or []
        failures = []
        for job in jobs:
            if not isinstance(job, dict):
                continue
            jc = str(job.get("conclusion") or "").lower()
            if jc in ("success", "skipped", "neutral"):
                continue
            steps = job.get("steps") or []
            failed_steps = [
                s
                for s in steps
                if isinstance(s, dict)
                and str(s.get("conclusion") or "").lower() in ("failure", "cancelled", "timed_out")
            ]
            for step in failed_steps:
                step_name = step.get("name", "?")
                log_tail = ""
                try:
                    _, lout, _ = run_gh(
                        [
                            "run",
                            "view",
                            run_id,
                            "--repo",
                            slug,
                            "--log-failed",
                            "--job",
                            str(job.get("databaseId") or job.get("id") or ""),
                        ],
                        timeout=60,
                    )
                    log_tail = lout[-4000:]
                except Exception:
                    log_tail = ""
                failures.append(
                    {
                        "job": job.get("name"),
                        "step": step_name,
                        "conclusion": jc,
                        "log_tail": log_tail,
                    }
                )
        return _ok(
            "workflow_view",
            {"run": data, "failures": failures, "failure_count": len(failures)},
        )

    if operation == "workflow_rerun":
        """Rerun a failed workflow run (or a single failed job)."""
        if not slug or not run_id:
            return _err("workflow_rerun", "owner, repo, run_id required")
        args = ["run", "rerun", run_id, "--repo", slug]
        if failed_job_id:
            args += ["--failed", "--job", str(failed_job_id)]
        ok, out, err = run_gh(args)
        if not ok:
            return _err("workflow_rerun", err or "workflow rerun failed")
        return _ok("workflow_rerun", {"run_id": run_id}, message="Workflow run rerun triggered")

    if operation == "workflow_disable":
        if not slug or not workflow_id:
            return _err("workflow_disable", "owner, repo, workflow_id required")
        ok, out, err = run_gh(["workflow", "disable", workflow_id, "--repo", slug])
        if not ok:
            return _err("workflow_disable", err or "workflow disable failed")
        return _ok("workflow_disable", {"workflow_id": workflow_id}, message="Workflow disabled")

    if operation == "workflow_enable":
        if not slug or not workflow_id:
            return _err("workflow_enable", "owner, repo, workflow_id required")
        ok, out, err = run_gh(["workflow", "enable", workflow_id, "--repo", slug])
        if not ok:
            return _err("workflow_enable", err or "workflow enable failed")
        return _ok("workflow_enable", {"workflow_id": workflow_id}, message="Workflow enabled")

    # ── Labels ────────────────────────────────────────────────────────────────
    if operation == "label_list":
        if not slug:
            return _err("label_list", "owner and repo required")
        ok, out, err = run_gh(["label", "list", "--repo", slug, "--json", "name,color,description"])
        if not ok:
            return _err("label_list", err or "label list failed")
        data = _j(out)
        return _ok("label_list", {"labels": data, "count": len(data)})

    if operation == "label_create":
        if not slug or not label_name:
            return _err("label_create", "owner, repo, label_name required")
        args = ["label", "create", label_name, "--repo", slug]
        if label_color:
            args += ["--color", label_color.lstrip("#")]
        if label_description:
            args += ["--description", label_description]
        ok, out, err = run_gh(args)
        if not ok:
            return _err("label_create", err or "label create failed")
        return _ok("label_create", {"name": label_name}, message=f"Label '{label_name}' created")

    if operation == "label_delete":
        if not slug or not label_name:
            return _err("label_delete", "owner, repo, label_name required")
        ok, out, err = run_gh(["label", "delete", label_name, "--repo", slug, "--yes"])
        if not ok:
            return _err("label_delete", err or "label delete failed")
        return _ok("label_delete", {"name": label_name}, message=f"Label '{label_name}' deleted")

    # ── Secrets ───────────────────────────────────────────────────────────────
    if operation == "secrets_list":
        if not slug:
            return _err("secrets_list", "owner and repo required")
        ok, out, err = run_gh(["secret", "list", "--repo", slug, "--json", "name,updatedAt"])
        if not ok:
            return _err("secrets_list", err or "secrets list failed")
        data = _j(out)
        return _ok("secrets_list", {"secrets": data, "count": len(data)})

    if operation == "secrets_set":
        if not slug or not secret_name or not secret_value:
            return _err("secrets_set", "owner, repo, secret_name, secret_value required")
        ok, out, err = run_gh(["secret", "set", secret_name, "--repo", slug, "--body", secret_value])
        if not ok:
            return _err("secrets_set", err or "secret set failed")
        return _ok("secrets_set", {"name": secret_name}, message=f"Secret '{secret_name}' set")

    if operation == "secrets_delete":
        if not slug or not secret_name:
            return _err("secrets_delete", "owner, repo, secret_name required")
        ok, out, err = run_gh(["secret", "delete", secret_name, "--repo", slug])
        if not ok:
            return _err("secrets_delete", err or "secret delete failed")
        return _ok("secrets_delete", {"name": secret_name}, message=f"Secret '{secret_name}' deleted")

    # ── Collaborators ─────────────────────────────────────────────────────────
    if operation == "collaborator_add":
        if not slug or not username:
            return _err("collaborator_add", "owner, repo, username required")
        ok, out, err = run_gh(
            [
                "api",
                f"repos/{slug}/collaborators/{username}",
                "--method",
                "PUT",
                "--field",
                f"permission={permission}",
            ]
        )
        if not ok:
            return _err(
                "collaborator_add",
                err or "collaborator add failed",
                recovery_options=["Check admin access", "gh auth login"],
            )
        return _ok(
            "collaborator_add",
            {"username": username, "permission": permission},
            message=f"{username} added as collaborator ({permission})",
        )

    if operation == "collaborator_remove":
        if not slug or not username:
            return _err("collaborator_remove", "owner, repo, username required")
        ok, out, err = run_gh(["api", f"repos/{slug}/collaborators/{username}", "--method", "DELETE"])
        if not ok:
            return _err("collaborator_remove", err or "collaborator remove failed")
        return _ok(
            "collaborator_remove",
            {"username": username},
            message=f"{username} removed as collaborator",
        )

    # ── Search ────────────────────────────────────────────────────────────────
    if operation == "search_repos":
        if not query:
            return _err("search_repos", "query required")
        ok, out, err = run_gh(
            [
                "search",
                "repos",
                query,
                "--limit",
                str(limit),
                "--json",
                (
                    "name,fullName,description,url,stargazerCount,language,"
                    "isPrivate,isFork,isArchived,updatedAt,repositoryTopics,defaultBranchRef"
                ),
            ]
        )
        if not ok:
            return _err("search_repos", err or "search failed")
        data = _j(out)
        return _ok(
            "search_repos",
            {"repos": data, "count": len(data), "query": query},
            next_steps=[
                "github_ops(operation='show_repo', owner='OWNER', repo='REPO')",
                "github_ops(operation='gitingest_link', owner='OWNER', repo='REPO')",
            ],
        )

    if operation == "search_issues":
        if not query:
            return _err("search_issues", "query required")
        ok, out, err = run_gh(
            [
                "search",
                "issues",
                query,
                "--limit",
                str(limit),
                "--json",
                "number,title,state,url,repository,author,createdAt",
            ]
        )
        if not ok:
            return _err("search_issues", err or "search failed")
        data = _j(out)
        return _ok("search_issues", {"issues": data, "count": len(data)})

    if operation == "search_code":
        if not query:
            return _err("search_code", "query required")
        ok, out, err = run_gh(
            [
                "search",
                "code",
                query,
                "--limit",
                str(limit),
                "--json",
                "path,repository,url,textMatches",
            ]
        )
        if not ok:
            return _err("search_code", err or "search failed")
        data = _j(out)
        if not isinstance(data, list):
            data = []
        res: dict[str, Any] = {"results": data, "count": len(data), "query": query}
        if pretty:
            md, uniq = format_code_search_markdown(data)
            res["markdown"] = md
            res["unique_repositories"] = uniq
        return _ok("search_code", res)

    if operation == "search_repos_topic":
        if not topic:
            return _err("search_repos_topic", "topic required (GitHub repo topic / tag)")
        qtopic = build_topic_repo_query(topic, owner, query)
        ok, out, err = run_gh(
            [
                "search",
                "repos",
                qtopic,
                "--limit",
                str(limit),
                "--json",
                (
                    "name,fullName,description,url,stargazerCount,language,"
                    "isPrivate,isFork,isArchived,updatedAt,repositoryTopics,defaultBranchRef"
                ),
            ]
        )
        if not ok:
            return _err("search_repos_topic", err or "search failed")
        data = _j(out)
        if not isinstance(data, list):
            data = []
        # Compute summary
        total = len(data)
        archived_count = sum(1 for r in data if r.get("isArchived", False))
        fork_count = sum(1 for r in data if r.get("isFork", False))
        return _ok(
            "search_repos_topic",
            {
                "repos": data,
                "count": total,
                "archived": archived_count,
                "forks": fork_count,
                "source_repos": total - fork_count,
                "built_query": qtopic,
                "topic": topic,
            },
            message=(f"{total} repos matching topic `{topic}` ({archived_count} archived, {fork_count} forks)"),
        )

    if operation == "search_repos_by_topic":
        if not topic:
            return _err("search_repos_by_topic", "topic required (GitHub repo topic / tag)")
        qtopic = build_topic_repo_query(topic, owner, query)
        ok, out, err = run_gh(
            [
                "search",
                "repos",
                qtopic,
                "--limit",
                str(limit),
                "--json",
                "name,fullName,description,url,stargazerCount,forkCount,"
                "language,isPrivate,isFork,updatedAt,pushedAt,repositoryTopics",
            ]
        )
        if not ok:
            return _err("search_repos_by_topic", err or "search failed")
        data = _j(out)
        if not isinstance(data, list):
            data = []
        return _ok(
            "search_repos_by_topic",
            {"repos": data, "count": len(data), "built_query": qtopic},
            message=f"Full-metadata repos matching topic `{topic}`",
        )

    if operation == "code_find_repos":
        built = build_code_find_query(
            query=query,
            owner=owner,
            extension=extension,
            path_pattern=path_pattern,
            search_scope=search_scope,
        )
        if not built:
            return _err(
                "code_find_repos",
                ("Provide query, or extension/path_pattern, or owner/search_scope to build a code search"),
                recovery_options=[
                    "github_ops(operation='code_find_repos', owner='YOU', extension='bak')",
                    ("github_ops(operation='search_code', query='extension:bak user:YOU', pretty=True)"),
                ],
            )
        ok, out, err = run_gh(
            [
                "search",
                "code",
                built,
                "--limit",
                str(limit),
                "--json",
                "path,repository,url,textMatches",
            ]
        )
        if not ok:
            return _err("code_find_repos", err or "code search failed")
        data = _j(out)
        if not isinstance(data, list):
            data = []
        md, uniq = format_code_search_markdown(data)
        return _ok(
            "code_find_repos",
            {
                "built_query": built,
                "results": data,
                "count": len(data),
                "markdown": md,
                "unique_repositories": uniq,
            },
            message=("Code search — see `markdown` for a skimmable table; `unique_repositories` lists affected repos"),
        )

    # ── GitHub Projects (gh project) ─────────────────────────────────────────
    if operation == "project_list":
        if not owner:
            return _err("project_list", "owner required (GitHub user or org, or @me)")
        ok, out, err = run_gh(["project", "list", "--owner", owner, "--limit", str(limit), "--format", "json"])
        if not ok:
            ok, out, err = run_gh(["project", "list", "--owner", owner, "--limit", str(limit)])
            if not ok:
                return _err(
                    "project_list",
                    err or "project list failed",
                    recovery_options=["gh auth refresh -s project", "Upgrade gh CLI"],
                )
            return _ok("project_list", {"raw": out.strip(), "owner": owner})
        pdata = _j(out)
        return _ok(
            "project_list",
            {
                "projects": pdata,
                "count": len(pdata) if isinstance(pdata, list) else 1,
                "owner": owner,
            },
        )

    if operation == "project_view":
        if not owner or project_number is None:
            return _err("project_view", "owner and project_number required")
        ok, out, err = run_gh(["project", "view", str(project_number), "--owner", owner, "--format", "json"])
        if not ok:
            ok, out, err = run_gh(["project", "view", str(project_number), "--owner", owner])
            if not ok:
                return _err("project_view", err or "project view failed")
            return _ok(
                "project_view",
                {"raw": out.strip(), "project_number": project_number, "owner": owner},
            )
        return _ok("project_view", _j(out) if isinstance(_j(out), (dict, list)) else {"raw": out.strip()})

    if operation == "project_create":
        if not owner or not title:
            return _err("project_create", "owner and title required")
        args = ["project", "create", "--owner", owner, "--title", title]
        if body:
            args += ["--body", body]
        ok, out, err = run_gh(args)
        if not ok:
            return _err(
                "project_create",
                err or "project create failed",
                recovery_options=["gh auth refresh -s project"],
            )
        return _ok(
            "project_create",
            {"output": (out + err).strip(), "owner": owner},
            message="Project created",
        )

    if operation == "project_delete":
        if not owner or project_number is None:
            return _err("project_delete", "owner and project_number required")
        ok, out, err = run_gh(["project", "delete", str(project_number), "--owner", owner])
        if not ok:
            return _err("project_delete", err or "project delete failed")
        return _ok(
            "project_delete",
            {"project_number": project_number, "owner": owner},
            message="Project deleted",
        )

    if operation == "project_edit":
        if not owner or project_number is None or not title:
            return _err("project_edit", "owner, project_number, and title (new title) required")
        ok, out, err = run_gh(["project", "edit", str(project_number), "--owner", owner, "--title", title])
        if not ok:
            return _err("project_edit", err or "project edit failed")
        return _ok(
            "project_edit",
            {"project_number": project_number, "owner": owner, "title": title},
            message="Project updated",
        )

    # ── GitHub Packages (gh api) ─────────────────────────────────────────────
    _pkg_types = frozenset({"npm", "maven", "rubygems", "docker", "nuget", "container"})

    if operation == "package_list":
        if not package_type:
            return _err(
                "package_list",
                "package_type required (npm, maven, rubygems, docker, nuget, container)",
            )
        pt = package_type.strip().lower()
        if pt not in _pkg_types:
            return _err("package_list", f"package_type must be one of: {', '.join(sorted(_pkg_types))}")
        if owner:
            path = f"orgs/{owner}/packages?package_type={pt}&per_page=100"
        else:
            path = f"user/packages?package_type={pt}&per_page=100"
        ok, out, err = run_gh(["api", path])
        if not ok:
            ok, out, err = run_gh(["api", path])
            if not ok:
                return _err(
                    "package_list",
                    err or "package list failed",
                    recovery_options=["gh auth refresh -s read:packages"],
                )
        data = _j(out)
        if not isinstance(data, list):
            data = [data] if data else []
        return _ok(
            "package_list",
            {"packages": data, "count": len(data), "package_type": pt, "owner": owner or "@me"},
        )

    if operation == "package_view":
        if not package_type or not package_name:
            return _err("package_view", "package_type and package_name required")
        pt = package_type.strip().lower()
        if pt not in _pkg_types:
            return _err("package_view", f"package_type must be one of: {', '.join(sorted(_pkg_types))}")
        pkg = package_name.strip()
        if owner:
            path = f"orgs/{owner}/packages/{pt}/{pkg}"
        else:
            path = f"user/packages/{pt}/{pkg}"
        ok, out, err = run_gh(["api", path])
        if not ok:
            return _err("package_view", err or "package view failed")
        return _ok("package_view", _j(out) if isinstance(_j(out), dict) else {"raw": out.strip()})

    if operation == "package_delete":
        if not package_type or not package_name:
            return _err("package_delete", "package_type and package_name required")
        pt = package_type.strip().lower()
        if pt not in _pkg_types:
            return _err("package_delete", f"package_type must be one of: {', '.join(sorted(_pkg_types))}")
        pkg = package_name.strip()
        if owner:
            path = f"orgs/{owner}/packages/{pt}/{pkg}"
        else:
            path = f"user/packages/{pt}/{pkg}"
        ok, out, err = run_gh(["api", "-X", "DELETE", path])
        if not ok:
            return _err(
                "package_delete",
                err or "package delete failed",
                recovery_options=["Needs write:packages + admin on org packages"],
            )
        return _ok(
            "package_delete",
            {"package": pkg, "package_type": pt, "owner": owner or "@me"},
            message="Package delete requested",
        )

    # ── Gitingest (digest URLs; no gh CLI) ───────────────────────────────────
    if operation == "gitingest_help":
        return _ok(
            "gitingest_help",
            {
                "markdown": GITINGEST_HELP_MARKDOWN,
                "links": {
                    "gitingest": "https://gitingest.com",
                    "upstream": "https://github.com/coderamp-labs/gitingest",
                    "llmstxt": "https://llmstxt.org/",
                },
            },
            message="Gitingest vs llms.txt — see markdown",
        )

    if operation == "gitingest_link":
        if not slug:
            return _err("gitingest_link", "owner and repo required")
        o, r = owner or "", repo or ""
        url = build_gitingest_url(o, r, ref=ref, subpath=subpath)
        gh = f"https://github.com/{slug}"
        if ref and subpath:
            gh = f"{gh}/tree/{ref}/{subpath.strip().strip('/')}"
        elif ref:
            gh = f"{gh}/tree/{ref}"
        elif subpath:
            gh = f"{gh}/tree/main/{subpath.strip().strip('/')}"
        return _ok(
            "gitingest_link",
            {
                "gitingest_url": url,
                "github_url": gh,
                "owner": o,
                "repo": r,
                "ref": ref,
                "subpath": subpath,
            },
            message="Open gitingest_url for an LLM-ready digest",
            next_steps=[f"github_ops(operation='show_repo', owner='{o}', repo='{r}')"],
        )

    if operation == "gitingest_convert_url":
        src = (github_url or query or "").strip()
        if not src:
            return _err(
                "gitingest_convert_url",
                "github_url required (or pass the URL as query)",
            )
        out_u, conv_err = github_url_to_gitingest(src)
        if conv_err or not out_u:
            return _err("gitingest_convert_url", conv_err or "convert failed")
        return _ok(
            "gitingest_convert_url",
            {"github_url": src, "gitingest_url": out_u},
            message="Paste gitingest_url into a browser or fetch for digest text",
        )

    return _err(operation, "Not implemented")
