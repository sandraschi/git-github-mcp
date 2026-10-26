"""Unit tests for GitHub search / repo card formatting helpers."""

from git_github_mcp.utils.github_format import (
    build_code_find_query,
    build_topic_repo_query,
    format_code_search_markdown,
    format_repo_card,
    gh_search_args,
    query_has_scope,
    query_wants_prs,
    split_search_query,
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


# -- gh search argv building (regression: multi-qualifier queries were passed as
#    one argv word, which gh quoted into a single phrase) ----------------------


def test_split_search_query_qualifiers() -> None:
    assert split_search_query("user:me updated:>=2026-10-23") == ["user:me", "updated:>=2026-10-23"]


def test_split_search_query_keeps_quoted_phrase() -> None:
    assert split_search_query('repo:o/r "fails on save" is:open') == ["repo:o/r", "fails on save", "is:open"]


def test_split_search_query_unbalanced_quote_falls_back() -> None:
    assert split_search_query('"oops is:open') == ['"oops', "is:open"]


def test_split_search_query_empty() -> None:
    assert split_search_query(None) == []
    assert split_search_query("   ") == []


def test_gh_search_args_flags_before_separator() -> None:
    args = gh_search_args("issues", "user:me -label:bug", ["--limit", "5"])
    assert args == ["search", "issues", "--limit", "5", "--", "user:me", "-label:bug"]


def test_scope_and_pr_detection() -> None:
    assert query_has_scope(["org:acme", "bug"])
    assert query_has_scope(["repo:o/r"])
    assert not query_has_scope(["bug", "is:open"])
    assert query_wants_prs(["is:pr"])
    assert query_wants_prs(["TYPE:PR"])
    assert not query_wants_prs(["is:issue"])
