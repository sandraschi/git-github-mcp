"""Red-shelf gate: confirmation token + working repo AI required for destructive MCP ops.

Contract (see docs/WRAPPEE.md "Delete all stale worktrees"): a vague
destructive must never sail straight through, and a bare confirm boolean
is forgeable by the model (Becket problem) — so execution needs a
single-use token echoed back. Only a round trip through the user can
complete the loop: pushback issues the token, the user relays it, the next
call echoes it with confirm=True.

MCP-side only — the webapp REST layer calls the implementations directly
(humans at the UI confirm by clicking).

Repo AI means a *local* LLM endpoint (Ollama :11434 or LM Studio :1234,
via capabilities.probe_local_llm). Cloud providers are separate ongoing
work (pioneered in arxiv-mcp) and deliberately out of scope here.

Tokens live in memory: restart invalidates them, expiry is 10 minutes.
"""

from __future__ import annotations

import logging
import secrets
import time
from typing import Any

from ..capabilities import probe_local_llm

logger = logging.getLogger("git-github-mcp.destructive_gate")

TOKEN_TTL_SECONDS = 600

# Exact operation names as implemented. Tight on purpose — extend only
# with a matching test in tests/test_destructive_gate.py.
# NOTE: repo_delete was removed from the MCP surface entirely (webapp/CLI
# only) — it is deliberately NOT in this set.
DESTRUCTIVE_GIT_BRANCH = frozenset({"branch_delete"})
DESTRUCTIVE_GIT_ADMIN = frozenset({"reset", "clean", "worktree_remove"})
DESTRUCTIVE_GITHUB = frozenset({"release_delete"})
# Everyday network ops are fine; only --force variants are destructive.
FORCE_GATED_NETWORK_OPS = frozenset({"push", "pull", "fetch", "clone"})

# Identifying args a token is bound to. A token echoed for different
# targets is rejected — "delete X" can never become "delete Y".
TARGET_KEYS = (
    "owner",
    "repo",
    "repo_path",
    "branch",
    "worktree_path",
    "tag_name",
    "remote",
    "commit",
    "issue_number",
    "pr_number",
)

_tokens: dict[str, dict[str, Any]] = {}


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


def _fingerprint(tool: str, operation: str, targets: dict[str, Any] | None) -> str:
    targets = targets or {}
    parts = [f"{k}={targets.get(k)}" for k in TARGET_KEYS if targets.get(k) is not None]
    return f"{tool}:{(operation or '').strip()}:" + ",".join(parts)


def _purge_expired(now: float) -> None:
    for token in [t for t, e in _tokens.items() if e["expires"] <= now]:
        del _tokens[token]


def issue_token(tool: str, operation: str, targets: dict[str, Any] | None) -> str:
    """Mint a single-use token bound to this exact call. 10-minute TTL."""
    now = time.monotonic()
    _purge_expired(now)
    token = secrets.token_urlsafe(24)
    _tokens[token] = {
        "fingerprint": _fingerprint(tool, operation, targets),
        "expires": now + TOKEN_TTL_SECONDS,
    }
    return token


def consume_token(token: str | None, tool: str, operation: str, targets: dict[str, Any] | None) -> bool:
    """True iff token is live, unexpired, and bound to this exact call.
    Single-use: consumed (popped) on success."""
    if not token:
        return False
    entry = _tokens.pop(token, None)
    if entry is None:
        return False
    if entry["expires"] <= time.monotonic():
        return False
    return entry["fingerprint"] == _fingerprint(tool, operation, targets)


def confirmation_required(
    tool: str,
    operation: str,
    *,
    candidates: Any = None,
    ai: dict[str, Any] | None = None,
    token: str | None = None,
    targets: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pushback payload: list, demand precision, echo the token, mitigate.
    No logging traceback — a refused destructive is routine, not a crash."""
    ai = ai if ai is not None else repo_ai_status()
    token = token if token is not None else issue_token(tool, operation, targets)
    out: dict[str, Any] = {
        "success": False,
        "operation": operation,
        "confirmation_required": True,
        "confirmation_token": token,
        "error": (
            f"Destructive operation '{operation}' ({tool}) needs explicit confirmation. "
            "Adjectives are not identifiers — name exact targets, then re-run with "
            "confirm=True AND confirm_token echoed back (single-use, 10 minutes, "
            "bound to these exact targets; a bare confirm=True without the token "
            "is refused — the model cannot grant itself permission)."
        ),
        "candidates": candidates,
        "repo_ai": ai,
        "recovery_options": [
            f'Re-run with exact identifiers, confirm=True and confirm_token="{token}"',
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
            "Start Ollama (`ollama serve`) or LM Studio with a model loaded, then retry with confirm=True and a fresh confirm_token",
            "Do it in the webapp as a human (REST endpoints are ungated)",
            "Cloud providers: separate ongoing work (pioneered in arxiv-mcp), not checked here",
        ],
    }


def gate(
    tool: str,
    operation: str,
    *,
    confirm: bool = False,
    confirm_token: str | None = None,
    force: bool = False,
    candidates: Any = None,
    targets: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Red-shelf gate. Returns None when execution may proceed, else the
    pushback/refusal payload. Safe ops always return None (no probe cost)."""
    if not is_destructive(tool, operation, force=force):
        return None
    ai = repo_ai_status()
    if consume_token(confirm_token, tool, operation, targets):
        if ai.get("works"):
            return None
        return ai_unavailable_refusal(tool, operation, ai=ai)
    return confirmation_required(tool, operation, candidates=candidates, ai=ai, targets=targets)
