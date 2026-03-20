"""github_ops portmanteau — validation without calling gh."""

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
