"""Fleet orchestrator — JSON-safe suite payloads."""

from __future__ import annotations

import json

from fastapi.encoders import jsonable_encoder

from git_github_mcp.services.fleet_orchestrator import op_council_payload


def test_council_payload_is_json_serializable() -> None:
    suite = {
        "generated_at": "2026-06-06T00:00:00+00:00",
        "morning_digest": {"success": True, "result": {"totals": {"stale_prs": 1, "notifications": 2}}},
        "ci_pulse": {"success": True, "result": {"failure_count": 0}},
    }
    council = op_council_payload(suite)
    suite["council_payload"] = council
    wrapped = {"success": True, "operation": "full_suite", "result": suite, "message": "ok"}

    json.dumps(wrapped)
    jsonable_encoder(wrapped)
