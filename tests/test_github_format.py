"""Unit tests for GitHub search / repo card formatting helpers."""

from git_github_mcp.utils.github_format import (
    build_code_find_query,
    build_topic_repo_query,
    format_code_search_markdown,
    format_repo_card,
)


def test_build_code_find_query_raw_only() -> None:
    assert (
        build_code_find_query(
            query="mcp language:python",
            owner=None,
            extension=None,
            path_pattern=None,
            search_scope=None,
        )
        == "mcp language:python"
    )


def test_build_code_find_query_owner_extension() -> None:
    q = build_code_find_query(
        query=None,
        owner="sandraschi",
        extension=".bak",
        path_pattern=None,
        search_scope=None,
    )
    assert "user:sandraschi" in q
    assert "extension:bak" in q


def test_build_code_find_query_path_and_text() -> None:
    q = build_code_find_query(
        query="dross",
        owner=None,
        extension=None,
        path_pattern="*.bak",
        search_scope="org:acme",
    )
    assert "org:acme" in q
    assert "path:*.bak" in q
    assert "dross" in q


def test_build_topic_repo_query() -> None:
    assert build_topic_repo_query("mcp", None, None) == "topic:mcp"
    q = build_topic_repo_query("fastmcp", "sandraschi", "stars:>1")
    assert "topic:fastmcp" in q
    assert "user:sandraschi" in q
    assert "stars:>1" in q


def test_format_repo_card_markdown() -> None:
    md = format_repo_card(
        {
            "name": "demo",
            "description": "A demo repo",
            "isPrivate": False,
            "stargazerCount": 3,
            "forkCount": 1,
            "url": "https://github.com/o/demo",
            "issues": {"totalCount": 0},
            "defaultBranchRef": {"name": "main"},
            "repositoryTopics": {"nodes": [{"name": "mcp"}]},
        },
        "markdown",
    )
    assert "# demo" in md
    assert "mcp" in md
    assert "https://github.com/o/demo" in md


def test_format_code_search_markdown_table() -> None:
    md, uniq = format_code_search_markdown(
        [
            {
                "path": "a.bak",
                "url": "https://github.com/o/r/blob/main/a.bak",
                "repository": {"nameWithOwner": "o/r"},
                "textMatches": [{"fragment": "noise"}],
            },
            {
                "path": "b.bak",
                "url": "https://github.com/o/r/blob/main/b.bak",
                "repository": {"nameWithOwner": "o/r"},
                "textMatches": [],
            },
        ]
    )
    assert "|" in md
    assert "o/r" in md
    assert uniq == ["o/r"]
