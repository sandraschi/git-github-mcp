"""Tests for git_ops."""

import tempfile
from pathlib import Path

import pytest

from git_github_mcp.tools.git_ops import git_ops


def test_git_ops_status_not_a_repo() -> None:
    """Status on non-repo returns error."""
    with tempfile.TemporaryDirectory() as tmp:
        result = git_ops(operation="status", repo_path=tmp)
    assert result["success"] is False
    assert "Not a Git repository" in result["error"]


def test_git_ops_unknown_operation() -> None:
    """Unknown operation returns error."""
    result = git_ops(operation="unknown")
    assert result["success"] is False
    assert "Unknown operation" in result["error"]


def test_git_ops_commit_needs_message() -> None:
    """Commit without message returns error."""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / ".git").mkdir()
        result = git_ops(operation="commit", repo_path=tmp)
    assert result["success"] is False
    assert "message required" in result["error"]


def test_git_ops_clone_needs_repo_url() -> None:
    """Clone without repo_url returns error."""
    result = git_ops(operation="clone")
    assert result["success"] is False
    assert "repo_url required" in result["error"]
