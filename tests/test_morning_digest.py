"""Morning digest helpers — no live gh calls."""

from __future__ import annotations

from git_github_mcp.services.morning_digest import (
    build_markdown_digest,
    classify_issue_stale,
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
        "repo_errors": [],
    }
    md = build_markdown_digest(summary)
    assert "GitHub fleet morning digest" in md
    assert "Stale PR" in md
    assert "New comment" in md


def test_run_morning_digest_requires_fleet(monkeypatch) -> None:
    monkeypatch.setattr(
        "git_github_mcp.services.morning_digest.load_fleet_repos",
        lambda **_: [],
    )
    result = run_morning_digest()
    assert result["success"] is False
    assert "No fleet repos" in (result.get("error") or "")
