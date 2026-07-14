"""Build /api/capabilities for fleet webapp introspection."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

logger = logging.getLogger("git-github-mcp.capabilities")

_PORTMANTEAU = frozenset(
    {
        "git_ops",
        "github_ops",
        "fleet_ops",
        "fleet_morning_digest",
        "git_agentic_workflow",
        "git_github_search_workflow",
    }
)


def _probe_local_llm() -> bool:
    for url in ("http://127.0.0.1:11434/api/tags", "http://127.0.0.1:1234/v1/models"):
        try:
            resp = httpx.get(url, timeout=1.2)
            if resp.status_code < 500:
                return True
        except Exception as exc:
            logger.debug("LLM probe failed for %s: %s", url, exc)
    return False


_STATIC_TOOLS = sorted(
    _PORTMANTEAU
    | {
        "git_github_status",
        "git_github_help",
    }
)


async def build_capabilities(mcp: Any, *, version: str = "0.4.0") -> dict[str, Any]:
    tool_names = list(_STATIC_TOOLS)
    try:
        tools = await mcp.list_tools(run_middleware=False)
        tool_names = sorted({t.name for t in tools})
    except Exception:
        logger.debug("list_tools failed, using static tool list")

    portmanteau_tools = [n for n in tool_names if n in _PORTMANTEAU]
    atomic_tools = [n for n in tool_names if n not in _PORTMANTEAU]

    prompt_names: list[str] = []
    try:
        prompts = await mcp.list_prompts()
        prompt_names = sorted({p.name for p in prompts})
    except Exception:
        prompt_names = []

    resource_uris: list[str] = []
    skill_uris: list[str] = []
    try:
        resources = await mcp.list_resources()
        for resource in resources:
            raw = getattr(resource, "uri", None) or getattr(resource, "name", "")
            uri = str(raw) if raw else ""
            if not uri:
                continue
            resource_uris.append(uri)
            if uri.startswith("skill://"):
                skill_uris.append(uri)
    except Exception:
        logger.debug("list_resources failed")

    local_llm = _probe_local_llm()

    return {
        "status": "ok",
        "server": {"name": "git-github-mcp", "version": version, "fastmcp": "3.4.2+"},
        "tool_surface": {
            "total": len(tool_names),
            "portmanteau_count": len(portmanteau_tools),
            "atomic_count": len(atomic_tools),
            "portmanteau_tools": portmanteau_tools,
            "atomic_tools": atomic_tools,
        },
        "features": {
            "sampling": True,
            "agentic_workflows": True,
            "prompts": len(prompt_names) > 0,
            "resources": len(resource_uris) > 0,
            "skills": len(skill_uris) > 0,
            "local_llm": local_llm,
            "local_llm_autodiscovery": True,
            "fleet_ops": True,
            "morning_digest": True,
        },
        "inventory": {
            "workflow_tools": ["git_agentic_workflow", "git_github_search_workflow"],
            "prompt_names": prompt_names,
            "resource_uris": sorted(resource_uris),
            "skill_uris": sorted(skill_uris),
        },
        "runtime": {
            "transport": "dual",
            "surface_mode": "portmanteau",
        },
        "timestamp": datetime.now(UTC).isoformat(),
    }
