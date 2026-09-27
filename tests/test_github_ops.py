"""github_ops portmanteau — validation without calling gh + discussions with mocked run_gh."""

import importlib
import json

import pytest

# NOTE: git_github_mcp.tools.__init__ re-exports the github_ops function,
# shadowing the submodule attribute — importlib gets the real module.
ops_mod = importlib.import_module("git_github_mcp.tools.github_ops")
from git_github_mcp.tools.github_ops import github_ops


def test_github_ops_unknown_operation() -> None:
    r = github_ops(operation="nope")
    assert r["success"] is False
    assert "Unknown operation" in (r.get("error") or "")


def test_code_find_repos_requires_criteria() -> None:
    r = github_ops(operation="code_find_repos")
    assert r["success"] is False
    assert r.get("operation") == "code_find_repos"


def test_search_repos_topic_requires_topic() -> None:
    r = github_ops(operation="search_repos_topic", owner="x")
    assert r["success"] is False


def test_show_repo_requires_slug() -> None:
    r = github_ops(operation="show_repo", owner="x")
    assert r["success"] is False


# ── Discussions: validation (no gh calls) ─────────────────────────────────


def test_discussion_ops_require_slug() -> None:
    for op in (
        "discussion_categories",
        "discussion_list",
        "discussion_view",
        "discussion_create",
        "discussion_comment",
        "discussion_answer",
        "discussion_lock",
        "discussion_unlock",
    ):
        r = github_ops(operation=op)
        assert r["success"] is False, op
        assert "owner and repo required" in (r.get("error") or ""), op


def test_discussion_view_requires_number() -> None:
    r = github_ops(operation="discussion_view", owner="o", repo="r")
    assert r["success"] is False
    assert "discussion_number required" in (r.get("error") or "")


def test_discussion_create_requires_fields() -> None:
    r = github_ops(operation="discussion_create", owner="o", repo="r", title="t")
    assert r["success"] is False
    assert "category, title and body required" in (r.get("error") or "")


def test_discussion_comment_requires_fields() -> None:
    r = github_ops(operation="discussion_comment", owner="o", repo="r")
    assert r["success"] is False
    assert "discussion_number and body required" in (r.get("error") or "")


def test_discussion_answer_requires_comment_id() -> None:
    r = github_ops(operation="discussion_answer", owner="o", repo="r")
    assert r["success"] is False
    assert "comment_id required" in (r.get("error") or "")


def test_discussion_lock_requires_number() -> None:
    r = github_ops(operation="discussion_lock", owner="o", repo="r")
    assert r["success"] is False
    assert "discussion_number required" in (r.get("error") or "")


# ── Discussions: mocked gh api graphql ────────────────────────────────────


def _payload(data: dict) -> str:
    return json.dumps(data)


class FakeGh:
    """Route canned GraphQL payloads by query/mutation substring."""

    def __init__(self, fail: bool = False, graphql_errors: bool = False):
        self.fail = fail
        self.graphql_errors = graphql_errors
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str], **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(args)
        query = next((a[len("query=") :] for a in args if a.startswith("query=")), "")
        if self.fail:
            return False, "", "oh no"
        if self.graphql_errors:
            return True, _payload({"errors": [{"message": "boom"}]}), ""
        if "createDiscussion" in query:
            return (
                True,
                _payload(
                    {"data": {"createDiscussion": {"discussion": {"number": 7, "url": "https://x/7", "title": "T"}}}}
                ),
                "",
            )
        if "addDiscussionComment" in query:
            return (
                True,
                _payload(
                    {
                        "data": {
                            "addDiscussionComment": {
                                "comment": {"id": "C1", "url": "https://x#c", "createdAt": "2026-09-19"}
                            }
                        }
                    }
                ),
                "",
            )
        if "markDiscussionCommentAsAnswer" in query:
            return (
                True,
                _payload(
                    {"data": {"markDiscussionCommentAsAnswer": {"discussion": {"number": 7, "isAnswered": True}}}}
                ),
                "",
            )
        if "unmarkDiscussionCommentAsAnswer" in query:
            return (
                True,
                _payload(
                    {"data": {"unmarkDiscussionCommentAsAnswer": {"discussion": {"number": 7, "isAnswered": False}}}}
                ),
                "",
            )
        if "lockLockable" in query or "unlockLockable" in query:
            return True, _payload({"data": {"lockLockable": {"lockedRecord": {"__typename": "Discussion"}}}}), ""
        if "bodyText" in query:
            return (
                True,
                _payload(
                    {
                        "data": {
                            "repository": {
                                "discussion": {
                                    "id": "D1",
                                    "number": 3,
                                    "title": "T",
                                    "url": "https://x/3",
                                    "bodyText": "B",
                                    "createdAt": "2026-09-19",
                                    "locked": True,
                                    "isAnswered": False,
                                    "category": {"name": "Announcements", "slug": "announcements"},
                                    "author": {"login": "me"},
                                    "comments": {
                                        "totalCount": 1,
                                        "nodes": [
                                            {
                                                "id": "C1",
                                                "author": {"login": "you"},
                                                "bodyText": "hi",
                                                "createdAt": "2026-09-19",
                                                "isAnswer": False,
                                                "upvoteCount": 2,
                                            }
                                        ],
                                    },
                                }
                            }
                        }
                    }
                ),
                "",
            )
        if "discussionCategories" in query:
            return (
                True,
                _payload(
                    {
                        "data": {
                            "repository": {
                                "discussionCategories": {
                                    "nodes": [
                                        {
                                            "id": "DIC_1",
                                            "name": "Announcements",
                                            "slug": "announcements",
                                            "emoji": ":mega:",
                                            "description": "d",
                                        },
                                        {
                                            "id": "DIC_2",
                                            "name": "Q&A",
                                            "slug": "q-a",
                                            "emoji": ":pray:",
                                            "description": "d",
                                        },
                                    ]
                                }
                            }
                        }
                    }
                ),
                "",
            )
        if "discussion(number" in query:
            return True, _payload({"data": {"repository": {"discussion": {"id": "D1"}}}}), ""
        if "discussions(" in query:
            return (
                True,
                _payload(
                    {
                        "data": {
                            "repository": {
                                "discussions": {
                                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                                    "nodes": [
                                        {
                                            "number": 3,
                                            "title": "Ann",
                                            "url": "https://x/3",
                                            "createdAt": "2026-09-19",
                                            "locked": True,
                                            "isAnswered": False,
                                            "upvoteCount": 0,
                                            "category": {"name": "Announcements", "slug": "announcements"},
                                            "author": {"login": "me"},
                                            "comments": {"totalCount": 0},
                                        },
                                        {
                                            "number": 4,
                                            "title": "Q",
                                            "url": "https://x/4",
                                            "createdAt": "2026-09-19",
                                            "locked": False,
                                            "isAnswered": True,
                                            "upvoteCount": 5,
                                            "category": {"name": "Q&A", "slug": "q-a"},
                                            "author": {"login": "you"},
                                            "comments": {"totalCount": 2},
                                        },
                                    ],
                                }
                            }
                        }
                    }
                ),
                "",
            )
        return True, _payload({"data": {"repository": {"id": "R1"}}}), ""


@pytest.fixture()
def fake_gh(monkeypatch: pytest.MonkeyPatch) -> FakeGh:
    fake = FakeGh()
    monkeypatch.setattr(ops_mod, "run_gh", fake)
    return fake


def test_discussion_categories_ok(fake_gh: FakeGh) -> None:
    r = github_ops(operation="discussion_categories", owner="o", repo="r")
    assert r["success"] is True
    assert r["result"]["count"] == 2
    assert r["result"]["categories"][0]["slug"] == "announcements"


def test_discussion_list_filter_category(fake_gh: FakeGh) -> None:
    r = github_ops(operation="discussion_list", owner="o", repo="r", category="q-a")
    assert r["success"] is True
    assert r["result"]["count"] == 1
    assert r["result"]["discussions"][0]["number"] == 4


def test_discussion_list_answered_only(fake_gh: FakeGh) -> None:
    r = github_ops(operation="discussion_list", owner="o", repo="r", answered_only=True)
    assert r["success"] is True
    assert r["result"]["count"] == 1
    assert r["result"]["discussions"][0]["isAnswered"] is True


def test_discussion_list_graphql_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ops_mod, "run_gh", FakeGh(graphql_errors=True))
    r = github_ops(operation="discussion_list", owner="o", repo="r")
    assert r["success"] is False
    assert "boom" in (r.get("error") or "")


def test_discussion_list_gh_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ops_mod, "run_gh", FakeGh(fail=True))
    r = github_ops(operation="discussion_list", owner="o", repo="r")
    assert r["success"] is False


def test_discussion_view_ok(fake_gh: FakeGh) -> None:
    r = github_ops(operation="discussion_view", owner="o", repo="r", discussion_number=3)
    assert r["success"] is True
    assert r["result"]["number"] == 3
    assert r["result"]["locked"] is True
    assert len(r["result"]["comments"]) == 1
    assert r["result"]["comments"][0]["id"] == "C1"


def test_discussion_create_flow(fake_gh: FakeGh) -> None:
    r = github_ops(
        operation="discussion_create",
        owner="o",
        repo="r",
        category="Announcements",
        title="T",
        body="B",
    )
    assert r["success"] is True
    assert r["result"]["number"] == 7
    assert r["result"]["category"] == "announcements"


def test_discussion_create_bad_category(fake_gh: FakeGh) -> None:
    r = github_ops(
        operation="discussion_create",
        owner="o",
        repo="r",
        category="nope",
        title="T",
        body="B",
    )
    assert r["success"] is False
    assert "unknown category" in (r.get("error") or "")
    assert "q-a" in (r.get("error") or "")


def test_discussion_comment_flow(fake_gh: FakeGh) -> None:
    r = github_ops(
        operation="discussion_comment",
        owner="o",
        repo="r",
        discussion_number=3,
        body="hello",
    )
    assert r["success"] is True
    assert r["result"]["id"] == "C1"
    assert r["result"]["discussion_number"] == 3


def test_discussion_answer_mark_unmark(fake_gh: FakeGh) -> None:
    r = github_ops(operation="discussion_answer", owner="o", repo="r", comment_id="C1")
    assert r["success"] is True
    assert r["result"]["answered"] is True
    r2 = github_ops(operation="discussion_answer", owner="o", repo="r", comment_id="C1", answered=False)
    assert r2["success"] is True
    assert r2["result"]["answered"] is False


def test_discussion_lock_unlock(fake_gh: FakeGh) -> None:
    r = github_ops(operation="discussion_lock", owner="o", repo="r", discussion_number=3)
    assert r["success"] is True
    assert r["result"]["locked"] is True
    r2 = github_ops(operation="discussion_unlock", owner="o", repo="r", discussion_number=3)
    assert r2["success"] is True
    assert r2["result"]["locked"] is False


def test_graphql_ints_use_typed_flag(fake_gh: FakeGh) -> None:
    # Ints must go via -F (typed) or GraphQL rejects them against Int!;
    # strings stay on -f (raw) so "123"-style values are never reinterpreted.
    github_ops(operation="discussion_list", owner="o", repo="r")
    flat = [a for call in fake_gh.calls for a in call]
    assert "-F" in flat
    idx = flat.index("-F")
    assert flat[idx + 1].startswith("first=")
    raw_vals = [flat[i + 1] for i, a in enumerate(flat[:-1]) if a == "-f" and not flat[i + 1].startswith("query=")]
    assert any(v.startswith("owner=") for v in raw_vals)
