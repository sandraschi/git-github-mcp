"""Gitingest URL helpers."""

from git_github_mcp.utils.gitingest_urls import (
    build_gitingest_url,
    github_url_to_gitingest,
)


def test_build_gitingest_url_root() -> None:
    assert build_gitingest_url("o", "r") == "https://gitingest.com/o/r"


def test_build_gitingest_url_strips_git_suffix() -> None:
    assert build_gitingest_url("o", "r.git") == "https://gitingest.com/o/r"


def test_build_gitingest_url_ref_and_subpath() -> None:
    u = build_gitingest_url(
        "sandraschi", "git-github-mcp", ref="main", subpath="src/git_github_mcp"
    )
    expected = "https://gitingest.com/sandraschi/git-github-mcp/tree/main/src/git_github_mcp"
    assert u == expected


def test_github_url_to_gitingest_repo() -> None:
    u, err = github_url_to_gitingest("https://github.com/foo/bar")
    assert err is None
    assert u == "https://gitingest.com/foo/bar"


def test_github_url_to_gitingest_tree() -> None:
    u, err = github_url_to_gitingest("https://github.com/foo/bar/tree/main/docs")
    assert err is None
    assert u == "https://gitingest.com/foo/bar/tree/main/docs"


def test_github_url_rejects_non_github() -> None:
    u, err = github_url_to_gitingest("https://gitlab.com/a/b")
    assert u is None
    assert err is not None
