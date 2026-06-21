"""Progress events for long-running fleet suite scans."""

from __future__ import annotations

from typing import Any, Callable

ProgressFn = Callable[[dict[str, Any]], None]

STEP_LABELS: dict[str, str] = {
    "morning_digest": "Morning digest",
    "registry_load": "Fleet registry",
    "mention_inbox": "Mention inbox",
    "ci_pulse": "CI pulse",
    "dependabot_digest": "Dependabot / security",
    "ack_drafts": "Acknowledgment drafts",
    "port_audit": "Port audit",
    "docs_gate": "Docs gate",
    "quarantine_report": "Quarantine report",
    "local_dirty": "Local workspace",
    "release_drift": "Release drift",
    "grade_snapshot": "Grade snapshot",
    "gitingest_bundle": "Gitingest links",
    "runner_status": "Runner status",
    "weekly_retro": "Weekly retro",
    "council_payload": "Council payload",
}


def suite_step_weights(repo_count: int) -> list[tuple[str, int]]:
    n = max(repo_count, 1)
    retro = min(repo_count, 40) if repo_count else 1
    return [
        ("morning_digest", n),
        ("registry_load", 1),
        ("mention_inbox", 1),
        ("ci_pulse", n),
        ("dependabot_digest", n),
        ("ack_drafts", n),
        ("port_audit", 1),
        ("docs_gate", 1),
        ("quarantine_report", 1),
        ("local_dirty", n),
        ("release_drift", n),
        ("grade_snapshot", 1),
        ("gitingest_bundle", 1),
        ("runner_status", 1),
        ("weekly_retro", retro),
        ("council_payload", 1),
    ]


class SuiteProgressTracker:
    """Weighted percent + step/repo labels for full_suite."""

    def __init__(self, repo_count: int, on_progress: ProgressFn | None) -> None:
        self.steps = suite_step_weights(repo_count)
        self.step_total = len(self.steps)
        self.step_weights = dict(self.steps)
        self.total_units = sum(weight for _, weight in self.steps)
        self.unit_offsets: dict[str, int] = {}
        offset = 0
        for step_id, weight in self.steps:
            self.unit_offsets[step_id] = offset
            offset += weight
        self.on_progress = on_progress
        self._step_index = 0
        self._current_step = ""

    def begin_step(self, step_id: str) -> None:
        self._step_index += 1
        self._current_step = step_id
        label = STEP_LABELS.get(step_id, step_id)
        self._emit(units_done_in_step=0, message=f"Starting {label}…")

    def step_done(self, step_id: str) -> None:
        weight = self.step_weights.get(step_id, 1)
        self._emit(units_done_in_step=weight, message=f"Finished {STEP_LABELS.get(step_id, step_id)}")

    def repo_tick(
        self,
        step_id: str,
        slug: str,
        index: int,
        total: int,
    ) -> None:
        label = STEP_LABELS.get(step_id, step_id)
        self._emit(
            units_done_in_step=index,
            repo=slug,
            repo_index=index,
            repo_total=total,
            message=f"{label}: {slug} ({index}/{total})",
        )

    def _emit(
        self,
        *,
        units_done_in_step: int,
        repo: str | None = None,
        repo_index: int | None = None,
        repo_total: int | None = None,
        message: str | None = None,
    ) -> None:
        if not self.on_progress or not self._current_step:
            return
        step_id = self._current_step
        step_weight = self.step_weights.get(step_id, 1)
        partial = max(0, min(units_done_in_step, step_weight))
        done_units = self.unit_offsets.get(step_id, 0) + partial
        percent = 100 if done_units >= self.total_units else int(100 * done_units / self.total_units)
        self.on_progress(
            {
                "percent": percent,
                "step": step_id,
                "step_label": STEP_LABELS.get(step_id, step_id),
                "step_index": self._step_index,
                "step_total": self.step_total,
                "repo": repo,
                "repo_index": repo_index,
                "repo_total": repo_total,
                "message": message,
            }
        )
