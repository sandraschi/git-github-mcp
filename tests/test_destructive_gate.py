"""Tests for the red-shelf destructive gate (MCP-side only).

The gate refuses vague destructives and all destructives without working
repo AI. Webapp REST bypasses the gate by calling implementations directly.
"""

import tempfile

from git_github_mcp.utils import destructive_gate as dg

AI_DOWN = {"works": False, "local_llm": False, "cloud": "not-configured", "detail": "down"}
AI_UP = {"works": True, "local_llm": True, "cloud": "not-configured", "detail": "up"}


def test_is_destructive_matrix() -> None:
    assert dg.is_destructive("git_admin", "worktree_remove") is True
    assert dg.is_destructive("git_admin", "reset") is True
    assert dg.is_destructive("git_admin", "clean") is True
    assert dg.is_destructive("git_branch", "branch_delete") is True
    assert dg.is_destructive("github_ops", "repo_delete") is True
    assert dg.is_destructive("github_ops", "release_delete") is True
    assert dg.is_destructive("git_core", "push", force=True) is True
    assert dg.is_destructive("git_core", "push") is False
    assert dg.is_destructive("git_core", "status") is False
    assert dg.is_destructive("git_admin", "worktree_list") is False
    assert dg.is_destructive("github_ops", "pr_list") is False
    assert dg.is_destructive("git_blame", "blame") is False
    assert dg.is_destructive("nope", "whatever") is False


def test_gate_allows_safe_ops_without_probe() -> None:
    # Safe ops return None before any AI probe (no network in this path).
    assert dg.gate("git_core", "status", confirm=False) is None
    assert dg.gate("github_ops", "pr_list", confirm=False) is None
    assert dg.gate("git_admin", "worktree_list", confirm=False) is None


def test_gate_no_confirm_pushback_mentions_ai_down(monkeypatch) -> None:
    monkeypatch.setattr(dg, "repo_ai_status", lambda: AI_DOWN)
    result = dg.gate("git_admin", "worktree_remove", confirm=False, candidates={"w": 1})
    assert result is not None
    assert result["success"] is False
    assert result["confirmation_required"] is True
    assert result["candidates"] == {"w": 1}
    assert "repo AI is not working" in result["error"]
    assert any("Ollama" in opt for opt in result["recovery_options"])


def test_gate_confirm_ai_down_refuses_canned(monkeypatch) -> None:
    monkeypatch.setattr(dg, "repo_ai_status", lambda: AI_DOWN)
    result = dg.gate("github_ops", "repo_delete", confirm=True)
    assert result is not None
    assert result["success"] is False
    assert "Refused" in result["error"]
    assert "repo AI is not working" in result["error"]
    assert any("webapp" in opt for opt in result["recovery_options"])


def test_gate_confirm_ai_up_allows(monkeypatch) -> None:
    monkeypatch.setattr(dg, "repo_ai_status", lambda: AI_UP)
    assert dg.gate("github_ops", "repo_delete", confirm=True) is None
    assert dg.gate("git_admin", "clean", confirm=True) is None


async def test_wrapper_git_admin_reset_no_confirm(monkeypatch) -> None:
    """MCP wrapper refuses before touching subprocesses."""
    from git_github_mcp import server

    monkeypatch.setattr(dg, "repo_ai_status", lambda: AI_DOWN)
    with tempfile.TemporaryDirectory() as tmp:
        result = await server.git_admin(operation="reset", repo_path=tmp, confirm=False)
    assert result["success"] is False
    assert result.get("confirmation_required") is True


async def test_wrapper_safe_op_passthrough() -> None:
    """Non-destructives flow through untouched (error here is from git itself)."""
    from git_github_mcp import server

    with tempfile.TemporaryDirectory() as tmp:
        result = await server.git_admin(operation="worktree_list", repo_path=tmp)
    assert "confirmation_required" not in result
