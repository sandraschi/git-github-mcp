# Contributing to git-github-mcp

Small fleet repo, one maintainer plus collaborators, zero patience for process theatre. These rules exist so your contribution gets merged instead of stalled.

## Issues first

- **Search before you file.** Duplicates get closed.
- **One issue, one request.** Two features = two issues.
- **Bug reports need the reproducer**: the `github_ops` operation and params (or exact `gh` command) plus the full error text.
- **Feature requests need a use case**: which repos, what workflow, what breaks today?

## Pull requests

- **File the issue first** (unless it's a trivial fix: typo, broken link, lint). The issue is where scope gets agreed before code exists.
- **Keep diffs small.** One concern per PR. Max 5 files per commit (10 per script invocation fleet-wide).
- **Tests required.** New behavior without a test is a draft, not a PR. Run `uv run pytest tests -q` before pushing (mock `run_gh` — see `tests/test_github_ops.py`).
- **Lint green:** `uv run ruff check src tests`.
- **The maintainer merges.** Don't merge your own PR. Note: default branch here is `master`.

## GitHub-ops rules: the hard parts

- **Portmanteau pattern**: one tool, `operation` enum — do not add dozens of atomic tools. New ops go in `tools/github_ops.py` with tests.
- **Destructive ops need the red-shelf gate** (`confirm=True` + token). Triage live actions additionally need explicit confirmation flags.
- **Every subprocess call carries a timeout** and never prompts (`GH_PROMPT_DISABLED`, stdin closed — see `utils/gh_cli.py`).
- **Timestamped `.bak` before any edit touching 3+ files.** Cleanup when satisfied.

## What this repo never does

- **No real `gh` calls in tests.** Mock at the `run_gh` boundary.
- **No secrets in code, tests, or examples.** Tokens come from env / `gh auth`, never strings.
- **No force-push to `master`.**
