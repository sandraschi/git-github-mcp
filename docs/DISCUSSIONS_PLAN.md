# Discussions support for git-github-mcp — Plan

Date: 2026-09-19. Status: IMPLEMENTED 2026-09-19 (uncommitted) — all phases
built and verified; see memops note "git-github-mcp discussions tools - decision".
Pilot verification: freecad-mcp discussions #3 (Announcements, locked), #4 (Q&A), #5 (General) created + locked via `gh api graphql` on 2026-09-19.

## 1. Why this closes a real gap

`github_ops` covers 61 actions across every major GitHub surface (repos, issues, PRs, releases, workflows, labels, secrets, collaborators, search, stars, projects, packages) except one: **Discussions**. There is no `gh discussion` subcommand — the only path is hand-rolled GraphQL (`createDiscussion`, category IDs, `lockLockable`, comment/answer mutations), which we proved works on 2026-09-19 but no agent should have to re-derive. Wrapping it in the portmanteau turns a 3-query manual procedure into one tool call, and it closes the loop on `mcp-central-docs/standards/GITHUB_DISCUSSIONS.md`: agents will be able to post/lock announcements and triage Q&A instead of only prescribing it in prose. Follow-up payoff (out of scope here): `fleet_morning_digest` surfacing unanswered Q&A per that standard's moderation-minimum rule.

## 2. Backend — 8 ops in `tools/github_ops.py` (portmanteau, no new tool)

- `discussion_categories` (list IDs/slugs — required input for create)
- `discussion_list` (paginated, filters: category, answered, locked)
- `discussion_view` (body + first-N comments)
- `discussion_create`, `discussion_comment`
- `discussion_answer` (mark comment as answer)
- `discussion_lock`, `discussion_unlock`

Implementation notes:

- Transport: `gh api graphql` via existing `utils/gh_cli.py::run_gh` (same pattern as package ops). Keep queries minimal (number/url/title/category/locked + comment count); paginate with `first`/`after` params per TOOL_DESIGN_STANDARDS.
- Verified 2026-09-19: categories query, `createDiscussion`, `lockLockable` (takes NO lockReason — discussions reject it, unlike issues). To verify during build: `addDiscussionComment`, `markDiscussionCommentAsAnswer`, list/view shapes, delete/close semantics.
- Destructive gate: check `utils/destructive_gate.py` first; create/comment/lock are reversible so expect no red-shelf gate, but follow file precedent.
- Update the module docstring action count (61 -> 69) and the tool description block.
- Docs sync in same change: `docs/TOOLS.md`, `llms.txt` / `llms-full.txt`, `glama.json` tool count.

## 3. Webapp — two pages + clickthrough fixes

**3a. New `/discussions` page** (`web/src/pages/discussions.tsx`): repo picker (owner/repo, default sandraschi/freecad-mcp), category filter chips, discussion list, detail view with comments, create form (category dropdown fed by `discussion_categories`), lock/unlock + mark-answer buttons. Route in `App.tsx`, sidebar entry (MessageSquare icon family — sidebar already imports it; pick non-colliding icon e.g. MessagesSquare), `data-testid` attributes per WEBAPP_SOTA_STANDARDS.

**3b. New repo-detail page `/repos/:owner/:repo`** (`web/src/pages/repo-detail.tsx`): the fleet repo inspector — GH situation in one place (stars, open issues, open PRs, discussions, latest release, workflow status) via existing ops + the new discussion ops, plus local `gitOps("status")` for the matching `D:/Dev/repos/<name>` checkout when present. This page does not exist today; `/repos` is a flat card grid whose only navigation is an external GitHub link on hover.

**3c. Clickthrough fixes (dead lists, confirmed 2026-09-19):** dashboard "Cloud Fleet" rows are plain divs, "Stars at a glance" top-repo chips are spans, "Recent Changes" entries are divs — none navigate anywhere. Wire Fleet rows + top-repo chips + `/repos` cards to the new repo-detail route. "Recent Changes" entries link to `/commits`. Use react-router `Link`, keep external-link icon for github.com.

## 4. Verification

- Backend: `ruff check`, `pytest` (new cases in `tests/test_github_ops.py` with mocked `run_gh`, modeled on `test_github_format.py`), live smoke against freecad-mcp discussions #3/#4/#5 (read-only ops only).
- Webapp: `tsc --noEmit`, `biome check`, browser pass (dashboard -> repo-detail -> discussions flow, create form against a test repo, never the pilot's locked announcement).
- Ship check: `just ci` equivalent per repo justfile; TOOLS.md + llms + glama.json synced.

## 5. Phasing (max 5 files per phase)

- Phase 1 (backend): `github_ops.py` (+ .bak first) + `tests/test_github_ops.py`.
- Phase 2 (docs sync): `docs/TOOLS.md`, docstring count, `llms.txt`, `llms-full.txt`, `glama.json`.
- Phase 3 (webapp): `discussions.tsx`, `repo-detail.tsx`, `App.tsx`, `sidebar.tsx`, `dashboard.tsx` (+ `repos.tsx` card links — split if over 5).
- Explicitly out of scope: fleet-wide `discussion_audit` op, morning-digest Q&A surfacing, upstream-wrappee posting automation.
