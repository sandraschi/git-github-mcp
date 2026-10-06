"""Morning digest helpers - no live gh calls."""

from __future__ import annotations

from datetime import UTC, datetime

from git_github_mcp.services.morning_digest import (
    build_markdown_digest,
    classify_discussion_signal,
    classify_issue_needs_reply,
    classify_pr_needs_reply,
    classify_pr_stale,
    fetch_issue_comments,
    last_maintainer_touch,
    parse_fleet_repos,
    run_morning_digest,
    scan_fleet_repo,
)


def test_classify_issue_needs_reply_fresh_external() -> None:
    """A real user report opened today with zero activity must surface -
    this was the inkscape-mcp #8 hole: age 0 < stale_days meant invisibility."""
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    issue = {
        "author": {"login": "NMDX0721"},
        "createdAt": now,
        "updatedAt": now,
        "number": 8,
        "title": "Windows: forcing LC_ALL breaks fontconfig",
        "url": "https://example.com/issues/8",
    }
    reason = classify_issue_needs_reply(issue, stale_days=7, maintainer="sandraschi")
    assert reason is not None
    assert "no maintainer reply" in reason or "today" in reason


def test_classify_issue_needs_reply_skips_maintainer() -> None:
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    issue = {"author": {"login": "sandraschi"}, "createdAt": now, "updatedAt": now}
    assert classify_issue_needs_reply(issue, stale_days=7, maintainer="sandraschi") is None


def test_classify_issue_needs_reply_skips_touched() -> None:
    """Any activity bump (comment, label) means it had eyes on it."""
    issue = {
        "author": {"login": "outsider"},
        "createdAt": "2026-09-01T00:00:00Z",
        "updatedAt": "2026-09-02T00:00:00Z",
    }
    assert classify_issue_needs_reply(issue, stale_days=30, maintainer="sandraschi") is None


def test_classify_issue_needs_reply_skips_stale_age() -> None:
    """Old untouched externals belong to stale_issues, not this bucket."""
    issue = {
        "author": {"login": "outsider"},
        "createdAt": "2020-01-01T00:00:00Z",
        "updatedAt": "2020-01-01T00:00:00Z",
    }
    assert classify_issue_needs_reply(issue, stale_days=7, maintainer="sandraschi") is None


def test_classify_pr_needs_reply_fresh_external() -> None:
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    pr = {
        "author": {"login": "contributor"},
        "createdAt": now,
        "updatedAt": now,
        "comments": 0,
        "number": 6,
        "title": "fix: docs",
        "url": "https://example.com/pr/6",
    }
    reason = classify_pr_needs_reply(pr, stale_days=7, maintainer="sandraschi")
    assert reason is not None


def test_classify_pr_needs_reply_skips_commented() -> None:
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    pr = {
        "author": {"login": "contributor"},
        "createdAt": now,
        "updatedAt": now,
        "comments": 2,
    }
    assert classify_pr_needs_reply(pr, stale_days=7, maintainer="sandraschi") is None


def test_build_markdown_digest_needs_reply_section() -> None:
    summary = {
        "generated_at": "2026-10-06T07:00:00+00:00",
        "maintainer": "sandraschi",
        "repo_count": 1,
        "stale_days": 7,
        "totals": {
            "open_prs": 0,
            "open_issues": 1,
            "stale_prs": 0,
            "stale_issues": 0,
            "needs_reply": 1,
            "notifications": 0,
            "dirty_repos": 0,
            "drift_repos": 0,
        },
        "notifications": [],
        "all_stale_prs": [],
        "all_stale_issues": [],
        "all_needs_reply": [
            {
                "repo_slug": "sandraschi/inkscape-mcp",
                "kind": "issue",
                "number": 8,
                "title": "Windows: forcing LC_ALL breaks fontconfig",
                "need_reply_reason": "opened today, no maintainer reply yet",
                "url": "https://github.com/sandraschi/inkscape-mcp/issues/8",
            }
        ],
        "local_dirty": {},
        "repo_errors": [],
    }
    md = build_markdown_digest(summary)
    assert "Needs first reply" in md
    assert "inkscape-mcp" in md
    assert "no maintainer reply yet" in md


def test_fetch_issue_comments_parses_gh_shape(monkeypatch) -> None:
    payload = {
        "comments": [
            {"author": {"login": "reporter"}, "createdAt": "2026-09-20T10:00:00Z"},
            {"author": {"login": "sandraschi"}, "createdAt": "2026-09-21T10:00:00Z"},
            "junk-entry",
        ]
    }

    import json as _json

    monkeypatch.setattr(
        "git_github_mcp.services.morning_digest.run_gh",
        lambda *_, **__: (True, _json.dumps(payload), ""),
    )
    ok, comments = fetch_issue_comments("sandraschi", "inkscape-mcp", 8)
    assert ok is True
    assert comments == [
        {"author": "reporter", "createdAt": "2026-09-20T10:00:00Z"},
        {"author": "sandraschi", "createdAt": "2026-09-21T10:00:00Z"},
    ]


def test_fetch_issue_comments_failure_degrades(monkeypatch) -> None:
    monkeypatch.setattr(
        "git_github_mcp.services.morning_digest.run_gh",
        lambda *_, **__: (False, "", "gh exploded"),
    )
    ok, comments = fetch_issue_comments("sandraschi", "inkscape-mcp", 8)
    assert ok is False
    assert comments == []


def test_fetch_issue_comments_bad_json(monkeypatch) -> None:
    monkeypatch.setattr(
        "git_github_mcp.services.morning_digest.run_gh",
        lambda *_, **__: (True, "not json{{{", ""),
    )
    ok, comments = fetch_issue_comments("sandraschi", "inkscape-mcp", 8)
    assert ok is False
    assert comments == []


def test_last_maintainer_touch_variants() -> None:
    issue = {"author": {"login": "reporter"}, "createdAt": "2026-09-01T00:00:00Z"}
    assert last_maintainer_touch(issue, [], maintainer="sandraschi") is None
    comments = [{"author": "reporter", "createdAt": "2026-09-20T10:00:00Z"}]
    assert last_maintainer_touch(issue, comments, maintainer="sandraschi") is None
    comments = [
        {"author": "reporter", "createdAt": "2026-09-20T10:00:00Z"},
        {"author": "SandraSchi", "createdAt": "2026-09-21T10:00:00Z"},
    ]
    assert last_maintainer_touch(issue, comments, maintainer="sandraschi") == "2026-09-21T10:00:00Z"
    own = {"author": {"login": "sandraschi"}, "createdAt": "2026-09-01T00:00:00Z"}
    assert last_maintainer_touch(own, [], maintainer="sandraschi") == "2026-09-01T00:00:00Z"
    assert last_maintainer_touch(issue, comments, maintainer=None) is None


def _bumped_issue() -> dict:
    """Reporter self-bump: created 20d ago, reporter commented yesterday.

    updatedAt moved, so both the stale check and the untouched heuristic pass
    it by - without comment depth it stays invisible forever.
    """
    from datetime import timedelta

    now = datetime.now(UTC)
    created = (now - timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%SZ")
    updated = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "author": {"login": "reporter"},
        "createdAt": created,
        "updatedAt": updated,
        "number": 9,
        "title": "Bumped by reporter",
        "url": "https://example.com/issues/9",
    }


def _scan_with(monkeypatch, issues, comments_fn) -> dict:
    def fake_github_ops(operation: str, **kwargs):
        if operation == "issue_list":
            return {"success": True, "result": {"issues": issues}}
        return {"success": True, "result": {"prs": []}}

    monkeypatch.setattr("git_github_mcp.services.morning_digest.github_ops", fake_github_ops)
    monkeypatch.setattr("git_github_mcp.services.morning_digest.fetch_issue_comments", comments_fn)
    return scan_fleet_repo(
        "sandraschi",
        "inkscape-mcp",
        stale_days=7,
        maintainer="sandraschi",
        limit=30,
        include_issues=True,
        include_discussions=False,
    )


def test_scan_reporter_bump_surfaces_via_comments(monkeypatch) -> None:
    def comments(owner: str, repo: str, number: int, **kwargs):
        assert (owner, repo, number) == ("sandraschi", "inkscape-mcp", 9)
        return True, [
            {"author": "reporter", "createdAt": "2026-09-20T10:00:00Z"},
            {"author": "reporter", "createdAt": "2026-09-21T10:00:00Z"},
            {"author": "reporter", "createdAt": "2026-09-22T10:00:00Z"},
        ]

    scanned = _scan_with(monkeypatch, [_bumped_issue()], comments)
    assert scanned["stale_issues"] == []
    assert len(scanned["needs_reply_issues"]) == 1
    row = scanned["needs_reply_issues"][0]
    assert row["need_reply_reason"] == "3 user comments, none from maintainer"
    assert row["comment_count"] == 3


def test_scan_maintainer_replied_stays_quiet(monkeypatch) -> None:
    from datetime import timedelta

    now = datetime.now(UTC)
    recent = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    def comments(owner: str, repo: str, number: int, **kwargs):
        return True, [
            {"author": "reporter", "createdAt": recent},
            {"author": "sandraschi", "createdAt": recent},
        ]

    scanned = _scan_with(monkeypatch, [_bumped_issue()], comments)
    assert scanned["stale_issues"] == []
    assert scanned["needs_reply_issues"] == []


def test_scan_maintainer_touch_gone_quiet_goes_stale(monkeypatch) -> None:
    """Maintainer replied once, long ago, reporter kept bumping since.

    Old code: reporter bumps reset updatedAt, thread never goes stale.
    New code: stale with a truthful reason.
    """

    def comments(owner: str, repo: str, number: int, **kwargs):
        return True, [
            {"author": "sandraschi", "createdAt": "2026-09-01T10:00:00Z"},
            {"author": "reporter", "createdAt": "2026-10-05T10:00:00Z"},
        ]

    scanned = _scan_with(monkeypatch, [_bumped_issue()], comments)
    assert scanned["needs_reply_issues"] == []
    assert len(scanned["stale_issues"]) == 1
    assert "maintainer last touched" in scanned["stale_issues"][0]["stale_reason"]


def test_scan_comment_fetch_failure_degrades(monkeypatch) -> None:
    def comments(owner: str, repo: str, number: int, **kwargs):
        return False, []

    scanned = _scan_with(monkeypatch, [_bumped_issue()], comments)
    assert scanned["stale_issues"] == []
    assert scanned["needs_reply_issues"] == []


def test_scan_comment_check_respects_limit(monkeypatch) -> None:
    seen: list[int] = []

    def comments(owner: str, repo: str, number: int, **kwargs):
        seen.append(number)
        return True, []

    issues = [{**_bumped_issue(), "number": n} for n in (1, 2, 3)]
    monkeypatch.setattr(
        "git_github_mcp.services.morning_digest.github_ops",
        lambda operation, **kwargs: (
            {"success": True, "result": {"issues": issues}}
            if operation == "issue_list"
            else {"success": True, "result": {"prs": []}}
        ),
    )
    monkeypatch.setattr("git_github_mcp.services.morning_digest.fetch_issue_comments", comments)
    scanned = scan_fleet_repo(
        "sandraschi",
        "inkscape-mcp",
        stale_days=7,
        maintainer="sandraschi",
        limit=30,
        include_issues=True,
        include_discussions=False,
        comment_check_limit=2,
    )
    assert seen == [1, 2]
    assert len(scanned["needs_reply_issues"]) == 2


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


def test_classify_discussion_signal_new_thread_and_unanswered_qa() -> None:
    node = {
        "createdAt": "2026-09-22T10:00:00Z",
        "updatedAt": "2026-09-22T10:00:00Z",
        "isAnswered": False,
        "locked": False,
        "category": {"name": "Q&A", "slug": "q-a", "isAnswerable": True},
    }
    since_dt = datetime(2026, 9, 20, tzinfo=UTC)
    has_new_activity, is_new_thread, is_unanswered_qa = classify_discussion_signal(node, since_dt=since_dt)
    assert has_new_activity is True
    assert is_new_thread is True
    assert is_unanswered_qa is True


def test_classify_discussion_signal_comment_on_old_thread() -> None:
    """A new comment on a discussion created before since_dt must still surface -
    this was the original bug: only createdAt was checked, so a comment on an
    old thread was invisible to the digest."""
    node = {
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-09-22T10:26:00Z",
        "isAnswered": False,
        "locked": False,
        "category": {"name": "Announcements", "slug": "announcements", "isAnswerable": False},
    }
    since_dt = datetime(2026, 9, 20, tzinfo=UTC)
    has_new_activity, is_new_thread, _ = classify_discussion_signal(node, since_dt=since_dt)
    assert has_new_activity is True
    assert is_new_thread is False


def test_classify_discussion_signal_old_and_non_qa() -> None:
    node = {
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-01T00:00:00Z",
        "isAnswered": False,
        "locked": False,
        "category": {"name": "Ideas", "slug": "ideas", "isAnswerable": False},
    }
    since_dt = datetime(2026, 9, 20, tzinfo=UTC)
    has_new_activity, is_new_thread, is_unanswered_qa = classify_discussion_signal(node, since_dt=since_dt)
    assert has_new_activity is False
    assert is_new_thread is False
    assert is_unanswered_qa is False


def test_classify_discussion_signal_answered_qa_not_flagged() -> None:
    node = {
        "createdAt": "2026-09-22T10:00:00Z",
        "updatedAt": "2026-09-22T10:00:00Z",
        "isAnswered": True,
        "locked": False,
        "category": {"name": "Q&A", "slug": "q-a", "isAnswerable": True},
    }
    since_dt = datetime(2026, 9, 20, tzinfo=UTC)
    _, _, is_unanswered_qa = classify_discussion_signal(node, since_dt=since_dt)
    assert is_unanswered_qa is False


def test_classify_discussion_signal_locked_qa_not_flagged() -> None:
    """A locked Q&A thread shouldn't nag the digest even if never marked answered."""
    node = {
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-01T00:00:00Z",
        "isAnswered": False,
        "locked": True,
        "category": {"name": "Q&A", "slug": "q-a", "isAnswerable": True},
    }
    since_dt = datetime(2026, 9, 20, tzinfo=UTC)
    _, _, is_unanswered_qa = classify_discussion_signal(node, since_dt=since_dt)
    assert is_unanswered_qa is False


def test_classify_discussion_signal_no_since_dt() -> None:
    """since_dt=None (first-ever run) should never flag anything as new."""
    node = {
        "createdAt": "2026-09-22T10:00:00Z",
        "updatedAt": "2026-09-22T10:00:00Z",
        "isAnswered": False,
        "locked": False,
        "category": {"name": "Q&A", "slug": "q-a", "isAnswerable": True},
    }
    has_new_activity, is_new_thread, _ = classify_discussion_signal(node, since_dt=None)
    assert has_new_activity is False
    assert is_new_thread is False


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


def test_build_markdown_digest_discussions_section() -> None:
    summary = {
        "generated_at": "2026-09-22T07:00:00+00:00",
        "maintainer": "sandraschi",
        "repo_count": 1,
        "stale_days": 7,
        "totals": {
            "open_prs": 0,
            "open_issues": 0,
            "stale_prs": 0,
            "stale_issues": 0,
            "discussions_open": 4,
            "new_discussions": 1,
            "unanswered_qa": 1,
            "notifications": 0,
            "dirty_repos": 0,
            "drift_repos": 0,
        },
        "notifications": [],
        "all_stale_prs": [],
        "all_stale_issues": [],
        "all_new_discussions": [
            {
                "repo_slug": "sandraschi/freecad-mcp",
                "number": 9,
                "title": "New idea from a user",
                "category": "Ideas",
                "author": "someuser",
                "activity_label": "new thread",
                "url": "https://github.com/sandraschi/freecad-mcp/discussions/9",
            },
            {
                "repo_slug": "sandraschi/sandraschi",
                "number": 1,
                "title": "Welcome - what this repo is",
                "category": "Announcements",
                "author": "sandraschi",
                "activity_label": "new replies",
                "url": "https://github.com/sandraschi/sandraschi/discussions/1",
            },
        ],
        "all_unanswered_qa": [
            {
                "repo_slug": "sandraschi/freecad-mcp",
                "number": 7,
                "title": "How do I do X?",
                "comments": 0,
                "url": "https://github.com/sandraschi/freecad-mcp/discussions/7",
            }
        ],
        "local_dirty": {},
        "repo_errors": [],
    }
    md = build_markdown_digest(summary)
    assert "Open discussions: **4**" in md
    assert "Discussion activity, new threads + comments (since last run): **1**" in md
    assert "Unanswered Q&A: **1**" in md
    assert "## Discussion activity (since last run)" in md
    assert "New idea from a user" in md
    assert "(new thread)" in md
    assert "(new replies)" in md
    assert "Welcome - what this repo is" in md
    assert "## Unanswered Q&A" in md
    assert "How do I do X?" in md


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
    # scan_fleet_repo mock above predates the discussions fields - must default
    # cleanly to zero/empty rather than KeyError.
    assert res["totals"]["discussions_open"] == 0
    assert res["totals"]["new_discussions"] == 0
    assert res["totals"]["unanswered_qa"] == 0
    # Same for the needs-first-reply bucket (mock predates those keys too).
    assert res["totals"]["needs_reply"] == 0
    assert res["all_needs_reply"] == []
