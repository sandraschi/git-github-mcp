"""Red-shelf gate: confirmation + working repo AI required for destructive MCP ops.

Contract (see docs/WRAPPEE.md "Delete all stale worktrees"): a vague
destructive must never sail straight through. The gate returns a pushback
payload (candidates, precision demand, mitigation hints) instead of
executing. MCP-side only — the webapp REST layer calls the implementations
directly (humans at the UI confirm by clicking).

Repo AI means a *local* LLM endpoint (Ollama :11434 or LM Studio :1234,
via capabilities.probe_local_llm). Cloud providers are separate ongoing
work and deliberately out of scope here.
"""

from __future__ import annotations

import logging
from typing import Any

from ..capabilities import probe_local_llm

logger = logging.getLogger("git-github-mcp.destructive_gate")

# Exact operation names as implemented. Tight on purpose — extend only
# with a matching test in tests/test_destructive_gate.py.
DESTRUCTIVE_GIT_BRANCH = frozenset({"branch_delete"})
DESTRUCTIVE_GIT_ADMIN = frozenset({"reset", "clean", "worktree_remove"})
DESTRUCTIVE_GITHUB = frozenset({"repo_delete", "release_delete"})
# Everyday network ops are fine; only --force variants are destructive.
FORCE_GATED_NETWORK_OPS = frozenset({"push", "pull", "fetch", "clone"})


def repo_ai_status() -> dict[str, Any]:
    """Working repo AI? Local probe only; cloud is separate ongoing work."""
    local = probe_local_llm()
    return {
        "works": local,
        "local_llm": local,
        "cloud": "not-configured",
        "detail": (
            "local LLM reachable (Ollama :11434 or LM Studio :1234)"
            if local
            else "no local LLM at 127.0.0.1:11434 or :1234; cloud providers not configured"
        ),
    }


def is_destructive(tool: str, operation: str, *, force: bool = False) -> bool:
    """True when (tool, operation) is on the red shelf."""
    op = (operation or "").strip()
    if tool == "git_branch":
        return op in DESTRUCTIVE_GIT_BRANCH
    if tool == "git_admin":
        return op in DESTRUCTIVE_GIT_ADMIN
    if tool == "github_ops":
        return op in DESTRUCTIVE_GITHUB
    if tool == "git_core":
        return force and op in FORCE_GATED_NETWORK_OPS
    return False


def confirmation_required(
    tool: str,
    operation: str,
    *,
    candidates: Any = None,
    ai: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pushback payload: list, demand precision, confirm, mitigate. No logging
    traceback — a refused destructive is routine, not a crash."""
    ai = ai if ai is not None else repo_ai_status()
    out: dict[str, Any] = {
        "success": False,
        "operation": operation,
        "confirmation_required": True,
        "error": (
            f"Destructive operation '{operation}' ({tool}) needs explicit confirmation. "
            "Adjectives are not identifiers — name exact targets and pass confirm=True."
        ),
        "candidates": candidates,
        "repo_ai": ai,
        "recovery_options": [
            f'Re-run with exact identifiers and confirm=True, e.g. {tool}(operation="{operation}", …, confirm=True)',
            "Define vague words first ('stale since when? merged already? whose?')",
            "Do it in the webapp as a human (REST is ungated)",
        ],
    }
    if not ai.get("works"):
        out["error"] += (
            " NOTE: repo AI is not working right now, so even a confirmed call "
            "will be refused until a local LLM answers — see mitigation below."
        )
        out["recovery_options"].append("Start Ollama (`ollama serve`) or LM Studio, then retry")
    return out


def ai_unavailable_refusal(tool: str, operation: str, *, ai: dict[str, Any] | None = None) -> dict[str, Any]:
    """Canned refusal: confirmed but repo AI is down. No execution, ever."""
    ai = ai if ai is not None else repo_ai_status()
    return {
        "success": False,
        "operation": operation,
        "confirmation_required": True,
        "repo_ai": ai,
        "error": (
            f"Refused '{operation}' ({tool}): repo AI is not working "
            f"({ai.get('detail')}). Destructive MCP operations need a working "
            "repo AI — this is the rule, not a suggestion."
        ),
        "recovery_options": [
            "Start Ollama (`ollama serve`) or LM Studio with a model loaded, then retry with confirm=True",
            "Do it in the webapp as a human (REST endpoints are ungated)",
            "Cloud providers: separate ongoing work, not checked here",
        ],
    }


def gate(
    tool: str,
    operation: str,
    *,
    confirm: bool = False,
    force: bool = False,
    candidates: Any = None,
) -> dict[str, Any] | None:
    """Red-shelf gate. Returns None when execution may proceed, else the
    pushback/refusal payload. Safe ops always return None (no probe cost)."""
    if not is_destructive(tool, operation, force=force):
        return None
    ai = repo_ai_status()
    if not confirm:
        return confirmation_required(tool, operation, candidates=candidates, ai=ai)
    if not ai.get("works"):
        return ai_unavailable_refusal(tool, operation, ai=ai)
    return None
