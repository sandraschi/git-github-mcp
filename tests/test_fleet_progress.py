"""Fleet suite progress tracker."""

from __future__ import annotations

from git_github_mcp.services.fleet_progress import SuiteProgressTracker


def test_progress_percent_increases() -> None:
    events: list[dict] = []

    tracker = SuiteProgressTracker(2, events.append)
    tracker.begin_step("morning_digest")
    tracker.repo_tick("morning_digest", "o/a", 1, 2)
    tracker.repo_tick("morning_digest", "o/b", 2, 2)
    tracker.step_done("morning_digest")
    tracker.begin_step("registry_load")
    tracker.step_done("registry_load")

    percents = [e["percent"] for e in events if "percent" in e]
    assert percents[0] == 0
    assert percents[-1] > percents[0]
    assert events[-1]["step"] == "registry_load"
