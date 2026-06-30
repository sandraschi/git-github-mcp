"""Fleet ops — registry parsing, port audit, dispatcher (no live gh)."""

from __future__ import annotations

import json
from pathlib import Path

from git_github_mcp.services.fleet_catalog import (
    _parse_webapp_ports_md,
    load_registry,
    op_port_audit,
    op_registry_load,
    registry_to_github_slugs,
)
from git_github_mcp.services.fleet_ops import OPERATIONS, fleet_ops


def test_operations_set() -> None:
    assert "full_suite" in OPERATIONS
    assert "registry_load" in OPERATIONS
    assert len(OPERATIONS) == 16


def test_fleet_ops_unknown_operation() -> None:
    res = fleet_ops("not_real")
    assert res["success"] is False
    assert "Unknown operation" in (res.get("error") or "")


def test_registry_to_github_slugs_skips_quarantined() -> None:
    entries = [
        {"id": "active-mcp", "status": "active"},
        {"id": "old-mcp", "status": "quarantined"},
        {"id": "deprecated-mcp", "status": "deprecated"},
    ]
    slugs = registry_to_github_slugs(entries, owner="sandraschi", active_only=True)
    assert slugs == [("sandraschi", "active-mcp")]


def test_parse_webapp_ports_md(tmp_path: Path) -> None:
    md = tmp_path / "WEBAPP_PORTS.md"
    md.write_text(
        "| Port | Repo | Notes |\n| 10702 | git-github-mcp | backend |\n| 10998 | scraper-mcp | api |\n",
        encoding="utf-8",
    )
    parsed = _parse_webapp_ports_md(md)
    assert 10702 in parsed["git-github-mcp"]
    assert 10998 in parsed["scraper-mcp"]


def test_port_audit_collisions(tmp_path: Path) -> None:
    reg = tmp_path / "fleet-registry.json"
    reg.write_text(
        json.dumps(
            {
                "fleet": [
                    {"id": "alpha-mcp", "port": 10700, "frontend_port": 10701},
                    {"id": "beta-mcp", "port": 10700, "frontend_port": 10702},
                ]
            }
        ),
        encoding="utf-8",
    )
    ports_md = tmp_path / "WEBAPP_PORTS.md"
    ports_md.write_text("| Port | Repo |\n", encoding="utf-8")
    res = op_port_audit(registry_path=str(reg), webapp_ports_path=str(ports_md))
    assert res["success"] is True
    result = res["result"]
    assert result["collision_count"] == 1
    assert result["collisions"][0]["port"] == 10700


def test_registry_load_missing(tmp_path: Path) -> None:
    missing = tmp_path / "nope.json"
    res = op_registry_load(registry_path=str(missing))
    assert res["success"] is False
    assert "not found" in (res.get("error") or "").lower()


def test_load_registry_empty_when_missing(tmp_path: Path) -> None:
    assert load_registry(tmp_path / "missing.json") == []
