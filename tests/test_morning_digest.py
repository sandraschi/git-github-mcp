"""Morning digest helpers — no live gh calls."""

from __future__ import annotations

from git_github_mcp.services.morning_digest import (
    build_markdown_digest,
    classify_pr_stale,
    parse_fleet_repos,
    run_morning_digest,
)


def test_parse_fleet_repos() -> None:
    text = """
    # comment
    sandraschi/git-github-mcp
    sandraschi/scraper-mcp
    bad-line
    """
    repos = parse_fleet_repos(text)
    assert repos == [("sandraschi", "git-github-mcp"), ("sandraschi", "scraper-mcp")]


def test_classify_pr_stale_no_comments() -> None:
    pr = {
        "author": {"login": "contributor"},
        "createdAt": "2020-01-01T00:00:00Z",
        "updatedAt": "2020-01-01T00:00:00Z",
        "comments": 0,
        "number": 1,
        "title": "Fix thing",
        "url": "https://example.com/pr/1",
    }
    reason = classify_pr_stale(pr, stale_days=7, maintainer="sandraschi")
    assert reason is not None
    assert "no comments" in reason


def test_classify_pr_stale_skips_maintainer() -> None:
    pr = {
        "author": {"login": "sandraschi"},
        "createdAt": "2020-01-01T00:00:00Z",
        "updatedAt": "2020-01-01T00:00:00Z",
        "comments": 0,
    }
    assert classify_pr_stale(pr, stale_days=7, maintainer="sandraschi") is None


def test_classify_pr_stale_gh_comments_list() -> None:
    """gh pr list --json comments returns comment objects, not a scalar count."""
    pr = {
        "author": {"login": "contributor"},
        "createdAt": "2020-01-01T00:00:00Z",
        "updatedAt": "2020-01-01T00:00:00Z",
        "comments": [{"id": "1"}, {"id": "2"}],
        "number": 2,
        "title": "Discussed PR",
        "url": "https://example.com/pr/2",
    }
    reason = classify_pr_stale(pr, stale_days=7, maintainer="sandraschi")
    assert reason is not None
    assert "quiet" in reason


def test_build_markdown_digest() -> None:
    summary = {
        "generated_at": "2026-06-05T07:00:00+00:00",
        "maintainer": "sandraschi",
        "repo_count": 2,
        "stale_days": 7,
        "totals": {
            "open_prs": 3,
            "open_issues": 1,
            "stale_prs": 1,
            "stale_issues": 0,
            "notifications": 2,
            "dirty_repos": 1,
            "drift_repos": 1,
        },
        "notifications": [
            {
                "repository": "sandraschi/git-github-mcp",
                "subject_title": "New comment",
                "reason": "comment",
                "subject_url": "https://github.com/sandraschi/git-github-mcp/pull/1",
                "unread": True,
            }
        ],
        "all_stale_prs": [
            {
                "repo_slug": "sandraschi/git-github-mcp",
                "number": 9,
                "title": "Stale PR",
                "stale_reason": "no comments in 14d",
                "url": "https://github.com/sandraschi/git-github-mcp/pull/9",
            }
        ],
        "all_stale_issues": [],
        "local_dirty": {
            "dirty": [
                {
                    "id": "git-github-mcp",
                    "repo_path": "D:/Dev/repos/git-github-mcp",
                    "changed_files": 2,
                    "sample": [" M src/foo.py", "?? bar.txt"],
                }
            ],
            "sync_drift": [
                {
                    "id": "git-github-mcp",
                    "repo_path": "D:/Dev/repos/git-github-mcp",
                    "ahead": 1,
                    "behind": 0,
                }
            ],
        },
        "repo_errors": [],
    }
    md = build_markdown_digest(summary)
    assert "GitHub fleet morning digest" in md
    assert "Stale PR" in md
    assert "New comment" in md
    assert "Dirty worktrees (uncommitted/untracked): **1**" in md
    assert "Sync drift (ahead/behind origin): **1**" in md
    assert "Local workspace hygiene (uncommitted work)" in md
    assert "git-github-mcp" in md
    assert "2 dirty file(s)" in md
    assert "Sync drift (ahead/behind origin)" in md
    assert "ahead 1, behind 0" in md


def test_run_morning_digest_requires_fleet(monkeypatch) -> None:
    monkeypatch.setattr(
        "git_github_mcp.services.morning_digest.load_fleet_repos",
        lambda **_: [],
    )
    result = run_morning_digest()
    assert result["success"] is False
    assert "No fleet repos" in (result.get("error") or "")


def test_run_morning_digest_mocked_local(monkeypatch) -> None:
    monkeypatch.setattr(
        "git_github_mcp.services.morning_digest.load_fleet_repos",
        lambda **_: [("sandraschi", "git-github-mcp")],
    )
    monkeypatch.setattr(
        "git_github_mcp.services.morning_digest.scan_fleet_repo",
        lambda *_, **__: {
            "slug": "sandraschi/git-github-mcp",
            "prs_open": 0,
            "issues_open": 0,
            "prs": [],
            "issues": [],
            "stale_prs": [],
            "stale_issues": [],
            "errors": [],
        },
    )
    monkeypatch.setattr(
        "git_github_mcp.services.morning_digest.fetch_notifications",
        lambda **_: [],
    )
    monkeypatch.setattr(
        "git_github_mcp.services.morning_digest.op_local_dirty",
        lambda **_: {
            "success": True,
            "result": {
                "dirty_count": 3,
                "sync_drift_count": 1,
                "dirty": [{"id": "test-repo", "changed_files": 2, "sample": [" M file.py"]}],
                "sync_drift": [{"id": "test-repo", "ahead": 1, "behind": 0}],
            },
        },
    )
    result = run_morning_digest(since_last_run=False)
    assert result["success"] is True
    res = result["result"]
    assert res["totals"]["dirty_repos"] == 3
    assert res["totals"]["drift_repos"] == 1
    assert "3 dirty worktrees" in result["message"]
    assert "Local workspace hygiene" in res["markdown"]
