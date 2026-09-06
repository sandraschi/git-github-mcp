# Wrappee: git + GitHub

This server drives two things you already know: **git** (local version
control) and **GitHub** (the forge where the code lives), via `git.exe`
and the `gh` CLI. No new concepts — the value is that your AI agent can
use them without tripping over PATH, auth, or subprocess hangs.

## A very short history

- **2005 — git**: Linus Torvalds writes git in weeks after the BitKeeper
  fallout, to carry Linux kernel development. Distributed by design: every
  clone is a full backup, branching is cheap, history is content-addressed.
- **2008 — GitHub**: hosting + pull requests + social coding turn git from
  a tool into a place. Fork → branch → PR → review becomes the default
  collaboration grammar of open source.
- **2018 — Microsoft acquires GitHub**: the forge stays the FOSS town
  square (the Linux kernel itself still lives by mailed patches, but nearly
  everything else — runtimes, frameworks, models — ships via GitHub).
- **`gh` CLI**: scriptable GitHub (repos, issues, PRs, releases, Actions)
  without browser-clicking — exactly what an agent needs.

## Usage patterns (porcelain → tool)

| You want | Tool call |
|----------|-----------|
| How dirty is this tree? | `git_core(operation="status", repo_path="…")` |
| What changed lately? | `git_core(operation="log", max_count=20)` |
| Start a feature | `git_branch(operation="branch_create", branch="feat/x")` |
| Undo safely / unsafely | `git_admin(operation="revert")` / `reset` |
| Find anything | `github_ops(operation="search_code", query="…")` |
| Triage the inbox | `github_ops(operation="pr_list", state="open")` |
| Ship | `github_ops(operation="release_create", tag_name="v…")` |
| Health of the fleet | `fleet_morning_digest()` / `fleet_ops(operation="full_suite")` |

## "Everybody knows git" means everybody knows a subset

git ships 150+ porcelain commands; `gh` spans repos, issues, PRs, releases,
Actions, packages, projects, search. Nobody holds all of it — most
developers live in `pull/commit/push` plus a few incantations copied from
long ago. You could accuse both tools of featuritis; the kinder truth is
they accreted 20 years of real workflows, sharp edges included.

This repo is a bit of a lecturer here. The dangerous corners are
first-class operations with guardrails and explanations, not footnotes:
`rebase`, `reset` vs `revert`, `cherry_pick`, force push, `bisect` — all
present in `git_branch` / `git_admin`, all taught in the in-app Lectures
(`/lectures`), all returning structured results with recovery options
instead of a mangled tree and silence. Rebase and force-push should not
elicit a "haaaah?" reaction — neither the operation nor the aftermath.

## AI on both sides of the pull request

A year ago the story was simple: AI-filed issues and PRs were mostly low
quality, and maintainers hated them — some repos posted blanket "no AI
contributions" notices. Then the models and agents got much stronger, and
the quality followed. The blanket refusal quietly became obsolete; what
nobody can reliably detect, nobody bothers to forbid, and increasingly
nobody wants to.

The healthier pattern won instead: solo devs and small teams now let their
own AI weed the inbox first — triage, acknowledge, reproduce — and spend
their human hours on judgment instead of janitorial reading. Everybody is
happy (we wish). The mood shifter has a name: Mythos. When it started surfacing
long-latent holes at scale — bugs and CVEs human reviewers had walked past
for years — it made mainstream news, and then a brouhaha: it didn't just
find the holes, it wrote working exploits. Goalposts moved weekly; access
was temporarily blocked while everyone argued whether a finder that also
forges weapons is a researcher or an arms dealer. The public-consumption
successor, Fable, ships guardrailed against exactly that — findings yes,
exploits no. The debate isn't settled, but the direction is: the machine
finds, the human decides.

This server is built for exactly that loop: `pr_list` with
comments/updatedAt for triage, `fleet_morning_digest` for the daily weed,
`ack_drafts` for the first reply. See [TOOLS.md](TOOLS.md).

## "Delete all stale worktrees" — words are sharper than they look

Try this on Claude Desktop with this server connected: *"delete all stale
worktrees in the repo."* Sounds like tidying. Could be a week's work gone
— because "stale" is doing an enormous amount of unexamined lifting. Stale
since when? Merged already? Whose? The sentence contains no answers, only
confidence.

This is where the repo AI earns its keep, if it works: a vague destructive
must never sail straight through to `worktree_remove`. The right response
is pushback in the tool result — *here are the worktrees, here is what
"stale" could mean for each, tell me exactly which ones, and here is how
you'd recover if I'm wrong* — list first, demand precision, confirm, and
attach mitigation hints. The response envelope already carries
`recovery_options` for exactly this; the discipline is using the plan step
for interrogation instead of obedience.

The red shelf, for reference: `worktree_remove`, `clean`, `reset`,
`branch_delete` — and `repo_delete`, which is exactly as final as it
sounds. Adjectives are not identifiers. Never `force` from a vague prompt.

## Why this is central to FOSS dev

Almost every dependency you have arrived via git + a forge: version tags
are releases, PRs are contributions, Actions are the CI this repo's own
exemplar workflow demonstrates. An agent that cannot do git is a
pair-programmer without hands. This server is those hands — plus the
maintainer loop (triage → digest → retro) that keeps 200+ repos alive.

## The Chinese alternative: Gitee

China's forge is [Gitee](https://gitee.com) — same git underneath,
different platform (faster domestically, its own API/auth). Our fleet
covers it the same way: **[gitee-mcp](https://github.com/sandraschi/gitee-mcp)**
is the Gitee counterpart of this server. If a dependency or mirror lives
on Gitee, use that repo instead of forcing GitHub-shaped calls onto it.

## Learn more (in this repo)

- **Lectures** — webapp `/lectures` page: git/GitHub/fleet/agent topics
  (rebase, merge-vs-rebase, cherry-pick, revert-vs-reset, stash, bisect,
  tracking upstream, …).
- **Help** — webapp `/help` page: page guide + agentic FAQ.
- **Tool reference** — [TOOLS.md](TOOLS.md); runtime help via the
  `git_github_help` tool.
- **Stuck?** — [TROUBLESHOOTING.md](TROUBLESHOOTING.md) (Problem → Cause → Fix).
- **Official docs** — [git-scm.com/doc](https://git-scm.com/doc) ·
  [cli.github.com/manual](https://cli.github.com/manual) ·
  [docs.github.com](https://docs.github.com).
