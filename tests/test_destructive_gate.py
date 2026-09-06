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
    assert dg.is_destructive("github_ops", "release_delete") is True
    # repo_delete was removed from the MCP surface (webapp/CLI only) — the
    # gate no longer sees it; the impl refuses with guidance instead.
    assert dg.is_destructive("github_ops", "repo_delete") is False
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
    assert isinstance(result.get("confirmation_token"), str)
    assert "repo AI is not working" in result["error"]
    assert any("Ollama" in opt for opt in result["recovery_options"])


def test_gate_confirm_ai_down_refuses_canned(monkeypatch) -> None:
    monkeypatch.setattr(dg, "repo_ai_status", lambda: AI_DOWN)
    targets = {"owner": "o", "repo": "r", "tag_name": "v1"}
    token = dg.issue_token("github_ops", "release_delete", targets)
    result = dg.gate("github_ops", "release_delete", confirm=True, confirm_token=token, targets=targets)
    assert result is not None
    assert result["success"] is False
    assert "Refused" in result["error"]
    assert "repo AI is not working" in result["error"]
    assert any("webapp" in opt for opt in result["recovery_options"])


def test_bare_confirm_without_token_refused(monkeypatch) -> None:
    """Bare confirm=True is the model granting itself permission — refused
    with a fresh token even when repo AI works (Becket rule)."""
    monkeypatch.setattr(dg, "repo_ai_status", lambda: AI_UP)
    result = dg.gate("github_ops", "release_delete", confirm=True)
    assert result is not None
    assert result["confirmation_required"] is True
    assert isinstance(result.get("confirmation_token"), str)


def test_token_dance_echo_executes(monkeypatch) -> None:
    """Pushback token echoed for identical targets + AI up => execution."""
    monkeypatch.setattr(dg, "repo_ai_status", lambda: AI_UP)
    targets = {"owner": "o", "repo": "r", "tag_name": "v1"}
    first = dg.gate("github_ops", "release_delete", targets=targets)
    assert first is not None
    token = first["confirmation_token"]
    assert dg.gate("github_ops", "release_delete", confirm=True, confirm_token=token, targets=targets) is None


def test_token_reuse_rejected(monkeypatch) -> None:
    """Single-use: the same token twice fails the second time."""
    monkeypatch.setattr(dg, "repo_ai_status", lambda: AI_UP)
    targets = {"owner": "o", "repo": "r", "tag_name": "v1"}
    token = dg.gate("github_ops", "release_delete", targets=targets)["confirmation_token"]
    assert dg.gate("github_ops", "release_delete", confirm=True, confirm_token=token, targets=targets) is None
    again = dg.gate("github_ops", "release_delete", confirm=True, confirm_token=token, targets=targets)
    assert again is not None
    assert again["confirmation_required"] is True


def test_token_bound_to_targets(monkeypatch) -> None:
    """A token for repo A echoed for repo B is refused (fresh token issued)."""
    monkeypatch.setattr(dg, "repo_ai_status", lambda: AI_UP)
    token = dg.gate("github_ops", "release_delete", targets={"owner": "o", "repo": "a"})["confirmation_token"]
    refused = dg.gate(
        "github_ops",
        "release_delete",
        confirm=True,
        confirm_token=token,
        targets={"owner": "o", "repo": "b"},
    )
    assert refused is not None
    assert refused["confirmation_token"] != token


def test_token_expiry_rejected(monkeypatch) -> None:
    monkeypatch.setattr(dg, "repo_ai_status", lambda: AI_UP)
    targets = {"owner": "o", "repo": "r"}
    token = dg.gate("github_ops", "release_delete", targets=targets)["confirmation_token"]
    dg._tokens[token]["expires"] = 0  # white-box: force expiry
    refused = dg.gate("github_ops", "release_delete", confirm=True, confirm_token=token, targets=targets)
    assert refused is not None
    assert refused["confirmation_required"] is True


def test_repo_delete_removed_from_surface() -> None:
    """repo_delete never reaches gh: impl refuses with webapp guidance."""
    from git_github_mcp.tools.github_ops import github_ops as impl

    result = impl(operation="repo_delete", owner="o", repo="r")
    assert result["success"] is False
    assert "removed from the MCP surface" in result["error"]
    assert any("webapp" in opt for opt in result["recovery_options"])


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


async def test_gate_plan_step_pops_confirm_and_passes_safe() -> None:
    """Plan helper strips confirm (impls don't accept it) and passes safe ops."""
    from git_github_mcp import server

    args, refusal = await server._gate_plan_step("git_ops", {"operation": "status", "confirm": True})
    assert args == {"operation": "status"}
    assert refusal is None


async def test_plan_step_token_echo_executes(monkeypatch) -> None:
    """Plan helper relays confirm_token; valid echo passes the gate."""
    from git_github_mcp import server

    monkeypatch.setattr(dg, "repo_ai_status", lambda: AI_UP)
    token = dg.issue_token("git_branch", "branch_delete", {"repo_path": ".", "branch": "x"})
    args, refusal = await server._gate_plan_step(
        "git_ops",
        {
            "operation": "branch_delete",
            "repo_path": ".",
            "branch": "x",
            "confirm": True,
            "confirm_token": token,
        },
    )
    assert refusal is None
    assert args == {"operation": "branch_delete", "repo_path": ".", "branch": "x"}


async def test_plan_executor_refuses_vague_destructive() -> None:
    """A planned 'delete all stale worktrees' stops at the gate, unexecuted."""
    import json
    from types import SimpleNamespace

    from git_github_mcp import server

    class FakeCtx:
        def __init__(self, text: str) -> None:
            self._text = text

        async def info(self, *a, **k) -> None:
            pass

        async def warning(self, *a, **k) -> None:
            pass

        async def sample(self, *a, **k):
            return SimpleNamespace(text=self._text)

    with tempfile.TemporaryDirectory() as tmp:
        plan = {
            "plan": "remove stale worktrees",
            "steps": [
                {
                    "tool": "git_ops",
                    "args": {
                        "operation": "worktree_remove",
                        "repo_path": tmp,
                        "worktree_path": "stale-one",
                    },
                    "description": "delete stale worktree",
                }
            ],
        }
        result = await server.git_agentic_workflow(
            task="delete all stale worktrees in the repo",
            repo_path=tmp,
            ctx=FakeCtx(json.dumps(plan)),
        )
    assert result["success"] is False
    step = result["results"][0]
    assert step["result"].get("confirmation_required") is True
