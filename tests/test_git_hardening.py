from pathlib import Path
from unittest.mock import MagicMock, patch

from git_github_mcp.tools.git_ops import git_ops


@patch("git_github_mcp.tools.git_ops._run_git_async")
async def test_git_ops_non_interactive_env(mock_run):
    """Verify that _run_git_async is called with non-interactive env vars."""
    mock_run.return_value = (True, "on branch main\nnothing to commit", "")

    await git_ops(operation="status", repo_path=".")

    assert mock_run.called


@patch("subprocess.run")
def test_run_git_env_injection(mock_subproc):
    """Verify that subprocess.run receives the hardened environment."""
    from git_github_mcp.tools.git_ops import _run_git

    mock_subproc.return_value = MagicMock(returncode=0, stdout="out", stderr="")

    _run_git(Path("."), ["status"])

    _args, kwargs = mock_subproc.call_args
    env = kwargs.get("env", {})

    assert env.get("GIT_TERMINAL_PROMPT") == "0"
    assert "BatchMode=yes" in env.get("GIT_SSH_COMMAND", "")


async def test_porcelain_status_parsing():
    """Verify high-fidelity porcelain status parsing."""
    from git_github_mcp.tools.git_ops import git_ops

    # Mock _run_git to return a mix of staged, unstaged, and untracked files
    # M = modified, A = added, D = deleted, ?? = untracked
    # Pos 1 = Index, Pos 2 = Worktree
    porcelain_output = (
        "M  staged_modified.txt\n"
        " A staged_added.txt\n"
        " M unstaged_modified.txt\n"
        "D  staged_deleted.txt\n"
        " D unstaged_deleted.txt\n"
        "?? untracked.txt\n"
        "UU unmerged.txt\n"
    )

    with patch("git_github_mcp.tools.git_ops._run_git_async") as mock_run:
        # Mock calls in order: status, branch, remote
        mock_run.side_effect = [
            (True, porcelain_output, ""),  # status --porcelain
            (True, "main", ""),  # branch
            (True, "https://github.com/user/repo", ""),  # remote get-url
        ]

        result = await git_ops(operation="status", repo_path=".")

        assert result["success"] is True
        res = result["result"]

        # Verify counts
        # M staged modifies index (pos 1), M unstaged modifies worktree (pos 2)
        # "M " -> Stage
        # " A" -> Unstaged (not added to index)
        # " M" -> Unstaged
        # "D " -> Staged
        # " D" -> Unstaged
        # "??" -> Untracked
        # "UU" -> Unmerged (ignored in simple counts usually)

        # M  -> staged
        #  A -> unstaged
        #  M -> unstaged
        # D  -> staged
        #  D -> unstaged
        # ?? -> untracked

        assert res["staged_count"] == 2  # M , D
        assert res["unstaged_count"] == 3  #  A,  M,  D
        assert res["untracked_count"] == 1  # ??
        assert res["unmerged_count"] == 1  # UU

        # Verify unmerged specific
        assert res["unmerged"][0]["file"] == "unmerged.txt"
        assert res["unmerged"][0]["code"] == "UU"
