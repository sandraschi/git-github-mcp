import {
  BookOpen,
  GitBranch,
  Github,
  GraduationCap,
  Search,
  Sparkles,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

type LectureCategory = "all" | "git" | "github" | "fleet" | "agents";

type Lecture = {
  key: string;
  category: Exclude<LectureCategory, "all">;
  title: string;
  subtitle: string;
  body: string[];
  tryThis?: string[];
  watchOut?: string[];
};

const CATEGORIES: {
  id: LectureCategory;
  label: string;
  Icon: typeof BookOpen;
}[] = [
  { id: "all", label: "All", Icon: GraduationCap },
  { id: "git", label: "Git", Icon: GitBranch },
  { id: "github", label: "GitHub", Icon: Github },
  { id: "fleet", label: "Fleet", Icon: BookOpen },
  { id: "agents", label: "Agents", Icon: Sparkles },
];

const LECTURES: Lecture[] = [
  {
    key: "rebase",
    category: "git",
    title: "Rebase",
    subtitle:
      "Replay your work on top of a fresher base — linear history, extra care.",
    body: [
      "Imagine you branched off main three days ago. Meanwhile main moved. Rebase picks up your commits one by one and replays them on top of the latest main, as if you had started today.",
      "Use it on feature branches you own. The payoff is a straight line of commits and cleaner reviews. The cost is conflict resolution during the replay — fix each stop, then continue.",
    ],
    tryThis: [
      "git fetch origin",
      "git rebase origin/main",
      "# after fixing conflicts:",
      "git rebase --continue",
      "# or bail out:",
      "git rebase --abort",
    ],
    watchOut: [
      "Never rebase commits other people already pulled unless the team explicitly works that way.",
      "After rebase you usually need a force push on your feature branch — coordinate before doing that on shared branches.",
    ],
  },
  {
    key: "merge-vs-rebase",
    category: "git",
    title: "Merge vs rebase",
    subtitle:
      "Two ways to combine branches — pick based on history politics, not dogma.",
    body: [
      'Merge says: "these two lines of history met here." You get a merge commit and an honest graph. Fine for long-lived branches and public main.',
      'Rebase says: "pretend my feature was always based on latest main." Cleaner log, rewritten SHAs. Fine for private feature branches before PR merge.',
      "Many teams merge PRs on GitHub (squash or merge commit) while rebasing locally during development. Both tools stay in the toolbox.",
    ],
    tryThis: ["git merge main", "git rebase main"],
  },
  {
    key: "cherry-pick",
    category: "git",
    title: "Cherry-pick",
    subtitle: "Steal one commit without merging the whole branch.",
    body: [
      "Production is on release-2.4 but the fix landed on main as commit abc123. Cherry-pick copies that patch onto your release branch as a new commit.",
      "Perfect for hotfixes and backports. Awkward when the same fix later merges wholesale — you may get duplicate changes or empty merges.",
    ],
    tryThis: ["git cherry-pick abc123", "git cherry-pick --abort"],
    watchOut: [
      "Context drift: a commit that applied cleanly on main may conflict on an older branch. Read the diff, don’t blindly trust the tool.",
    ],
  },
  {
    key: "revert-vs-reset",
    category: "git",
    title: "Revert vs reset",
    subtitle:
      "Undo mistakes on shared history without gaslighting your teammates.",
    body: [
      "Revert builds a new commit that undoes a bad one. History stays intact; everyone can pull safely. This is what you want on main.",
      "Reset moves the branch pointer backward. Soft reset keeps files staged; hard reset throws away working tree changes. Powerful, private, dangerous on pushed branches.",
    ],
    tryThis: [
      "git revert <sha>",
      "git reset --soft HEAD~1",
      "git reset --hard <sha>  # local only!",
    ],
    watchOut: [
      "Hard reset on shared branches forces others to recover manually. Prefer revert for anything already on GitHub.",
    ],
  },
  {
    key: "stash",
    category: "git",
    title: "Stash",
    subtitle: "Park uncommitted work without committing fiction.",
    body: [
      "You’re mid-edit but need to switch branches to review a hotfix. Stash snapshots your dirty tree, cleans the working copy, and lets you pop it back later.",
      'Name stashes when you have more than one (`git stash push -m "wip auth refactor"`). List before you pop so you don’t apply the wrong snapshot.',
    ],
    tryThis: ['git stash push -m "wip"', "git stash list", "git stash pop"],
  },
  {
    key: "bisect",
    category: "git",
    title: "Bisect",
    subtitle:
      "Binary search through history to find which commit broke the build.",
    body: [
      "Tests passed last Tuesday, fail today. Bisect checks out the middle commit, you mark good or bad, git jumps halfway again until it isolates the culprit.",
      "Tedious by hand; git automates the partitioning. Best when you have a reliable test command (one-liner exit code).",
    ],
    tryThis: [
      "git bisect start",
      "git bisect bad",
      "git bisect good <last-known-good-sha>",
      "# test each step, then:",
      "git bisect good # or bad",
      "git bisect reset",
    ],
  },
  {
    key: "upstream",
    category: "git",
    title: "Tracking upstream",
    subtitle: "Why `git pull` sometimes works and sometimes asks for `-u`.",
    body: [
      "The first push of a new branch needs `git push -u origin feature/foo` so local `feature/foo` knows its remote partner. After that, plain `git pull` and `git push` know where to talk.",
      'MCP: `git_core(operation="push", set_upstream=true)` on first publish. `git status` often hints when upstream is missing.',
    ],
    tryThis: ["git push -u origin my-branch", "git branch -vv"],
  },
  {
    key: "worktree",
    category: "git",
    title: "Worktrees",
    subtitle: "Two branches checked out at once without cloning twice.",
    body: [
      "Main repo stays on feature-A; add a worktree folder for a quick hotfix on main. Each worktree has its own working directory but shares git object database.",
      "Useful when agents or you need parallel checkouts. Remember which folder is which — easy to commit in the wrong tree.",
    ],
    tryThis: [
      "git worktree add ../hotfix-main main",
      "git worktree list",
      "git worktree remove ../hotfix-main",
    ],
  },
  {
    key: "pr-lifecycle",
    category: "github",
    title: "Pull request lifecycle",
    subtitle: "From branch push to merge — what maintainers actually look at.",
    body: [
      "Push a branch, open a PR, get review, fix CI, merge. Draft PRs signal WIP. Stale PRs with no discussion are what Breakfast flags — someone should ack or close.",
      "Via MCP: `pr_list` to scan, `pr_view` for detail, `pr_comment` to reply. Merge through `pr_merge` when checks are green and policy allows.",
    ],
    tryThis: [
      'github_ops(operation="pr_list", owner="…", repo="…", state="open")',
      'github_ops(operation="pr_create", owner="…", repo="…", title="…", head_branch="feature/x")',
    ],
  },
  {
    key: "draft-prs",
    category: "github",
    title: "Draft pull requests",
    subtitle: 'Signal "not ready for review" without hiding the branch.',
    body: [
      "Draft PRs appear in lists but reviewers know not to nitpick yet. Convert to ready when CI and description are solid.",
      "Fleet stale logic still sees old draft PRs — if it sits for weeks, close or update intentionally.",
    ],
  },
  {
    key: "github-actions",
    category: "github",
    title: "GitHub Actions debugging",
    subtitle: "When CI is red and the log wall is ten thousand lines.",
    body: [
      "Start from the failed job name and the first error line, not the tail of the log. `workflow_runs` in MCP lists recent conclusions; open the HTML URL for full detail.",
      "Re-run failed jobs after fixing flaky infra. Disable workflows you don't own with care — `workflow_disable` is destructive to automation.",
    ],
    tryThis: [
      'github_ops(operation="workflow_runs", owner="…", repo="…", limit=5)',
    ],
    watchOut: [
      "Fleet ci_pulse only surfaces failures in the last 48h — older red builds need manual history.",
    ],
  },
  {
    key: "dependabot",
    category: "github",
    title: "Dependabot and security alerts",
    subtitle: "Noise vs real risk — how fleet digest helps.",
    body: [
      "Dependabot opens version bump PRs; security advisories flag CVEs. Not every alert needs immediate merge — triage by severity and exploitability.",
      "Breakfast `dependabot_digest` aggregates open alerts across the fleet so you don't open sixty repos manually.",
    ],
    tryThis: ['fleet_ops(operation="dependabot_digest", use_registry=true)'],
  },
  {
    key: "github-projects",
    category: "github",
    title: "GitHub Projects",
    subtitle:
      "Boards and fields at org or user scope — not the same as repo Projects classic.",
    body: [
      "Projects v2 track issues and PRs across repos with custom fields. Useful for maintainer kanban; agents can list and create via `project_*` operations.",
      "gh needs project scope — refresh auth if calls fail with permission errors.",
    ],
    tryThis: [
      "gh auth refresh -s project",
      "gh project list --owner @me",
      'github_ops(operation="project_list", owner="sandraschi")',
    ],
    watchOut: [
      "Project numbers are scoped per owner — always pass the right org or user.",
    ],
  },
  {
    key: "github-packages",
    category: "github",
    title: "GitHub Packages",
    subtitle: "Container, npm, maven registries tied to repos and orgs.",
    body: [
      "Packages live beside code: publish on release, consume in Actions. MCP exposes list/view/delete for housekeeping (old container tags pile up).",
      "Deleting packages needs appropriate token scopes — read is not enough for cleanup.",
    ],
    tryThis: ['github_ops(operation="package_list", owner="sandraschi")'],
    watchOut: [
      "Org package deletes may need admin — test on a sandbox package first.",
    ],
  },
  {
    key: "code-search",
    category: "github",
    title: "Search across the fleet",
    subtitle: "Find repos, issues, or literal code needles.",
    body: [
      '`search_repos` and `search_issues` wrap gh search syntax. `code_find_repos` and `search_code` help answer "where do we still have .bak files" or "who imports legacy_module".',
      "For LLM-planned discovery chains, use `git_github_search_workflow` when your MCP host supports sampling.",
    ],
    tryThis: [
      'github_ops(operation="search_repos", query="topic:mcp user:sandraschi")',
      'github_ops(operation="code_find_repos", owner="sandraschi", extension="bak")',
    ],
  },
  {
    key: "gitingest",
    category: "github",
    title: "Gitingest — repo digest for LLMs",
    subtitle: "One URL turns a tree into prompt-friendly text.",
    body: [
      "Rule of thumb: replace `hub` with `ingest` in github.com URLs. Gitingest returns directory structure plus file contents sized for model context — good before a big refactor ask.",
      "Public repos work out of the box; private repos need a PAT in Gitingest or the CLI. It complements — not replaces — curated `llms.txt` in fleet repos.",
    ],
    tryThis: [
      "Open https://gitingest.com/sandraschi/git-github-mcp",
      'github_ops(operation="gitingest_url", owner="sandraschi", repo="git-github-mcp")',
      "pipx install gitingest — gitingest https://github.com/owner/repo",
    ],
    watchOut: [
      "Huge monorepos can exceed context — narrow with `subpath` when the tool supports it.",
    ],
  },
  {
    key: "fork-and-upstream",
    category: "github",
    title: "Forks and upstream sync",
    subtitle:
      "Contributing to someone else's repo without losing your remotes.",
    body: [
      "Fork on GitHub, clone your fork, add `upstream` pointing at the source repo. Pull from upstream main, push to your origin, open PR from your fork.",
      "MCP `repo_fork` and `repo_clone` automate pieces; you still think in remotes when syncing long-lived forks.",
    ],
    tryThis: [
      "git remote add upstream https://github.com/original/repo.git",
      "git fetch upstream",
      "git merge upstream/main",
    ],
  },
  {
    key: "breakfast",
    category: "fleet",
    title: "Breakfast runner",
    subtitle: "Morning maintainer pass over the whole MCP fleet.",
    body: [
      "Not a cron inside the server — a ritual you or a supervisor agent runs. Scans PRs, issues, notifications, CI, Dependabot, ports, docs gates, dirty clones.",
      "Web UI shows live progress per repo. Full registry ≈ ten minutes; start with two repos while learning.",
    ],
    tryThis: [
      "Open /breakfast → Start full suite",
      'fleet_ops(operation="full_suite", use_registry=true)',
    ],
  },
  {
    key: "fleet-list",
    category: "fleet",
    title: "Fleet list format",
    subtitle: "One owner/repo per line — shared everywhere.",
    body: [
      "Lines like `sandraschi/git-github-mcp` with optional `# comments`. Used in Breakfast, Inbox, and morning digest MCP args.",
      "Load from mcp-central-docs registry when you want the full ~140 repos; paste a short list when debugging one feature.",
    ],
    tryThis: [
      'fleet_morning_digest(fleet_repos="sandraschi/foo\\nsandraschi/bar")',
    ],
  },
  {
    key: "council-payload",
    category: "fleet",
    title: "Council payload",
    subtitle: "JSON summary for supervisor agents after a suite run.",
    body: [
      "After `full_suite`, `council_payload` compresses stale PR count, CI failures, dirty repos, and suggested actions into one object for robofang-style orchestrators.",
      "Human equivalent: the overview tiles on the Breakfast page after a run completes.",
    ],
  },
  {
    key: "port-audit",
    category: "fleet",
    title: "Port collisions",
    subtitle: "Why two MCP webapps can't share 10713.",
    body: [
      "Fleet registry and WEBAPP_PORTS.md should agree on backend/frontend ports. `port_audit` finds duplicates before you wonder why Vite proxies to the wrong server.",
      "Zombie processes on Windows often hold ports — `web\\start.bat` kills listeners before restart.",
    ],
    tryThis: ['fleet_ops(operation="port_audit")'],
  },
  {
    key: "gh-auth",
    category: "fleet",
    title: "gh authentication",
    subtitle: "The single dependency under half the fleet tools.",
    body: [
      "Run `gh auth login` once in a normal terminal. MCP and Breakfast delegate to gh — no separate API key in server config.",
      'If Breakfast returns empty GitHub data but "succeeds", auth is the first suspect. `git_github_status` surfaces login state for agents.',
    ],
    tryThis: ["gh auth status", 'github_ops(operation="auth_status")'],
  },
  {
    key: "portmanteau",
    category: "agents",
    title: "Portmanteau MCP tools",
    subtitle: "Why agents pass `operation=` instead of calling ninety tools.",
    body: [
      "Large tool lists confuse models and blow context. git-github-mcp groups operations: `github_ops`, `git_core`, `fleet_ops`. Same HTTP bridge, same shapes.",
      "Always read `success` in the response. Errors include `recovery_options` written for both human and model.",
    ],
    tryThis: ['git_github_help(level="basic", topic="github_ops")'],
  },
  {
    key: "sampling-workflows",
    category: "agents",
    title: "Agentic sampling workflows",
    subtitle: "When the host LLM plans, the server executes.",
    body: [
      "`git_agentic_workflow` — natural language → planned git + GitHub steps. `git_github_search_workflow` — discovery presets with LLM-chosen queries.",
      "Requires MCP sampling (Cursor, Antigravity-class hosts). Without it, chain `github_ops` manually or use web /api/discovery presets.",
    ],
  },
  {
    key: "prompts",
    category: "agents",
    title: "MCP prompts",
    subtitle: "Structured templates for commits, PRs, releases, reviews.",
    body: [
      "Seven prompts ship with the server: commit messages from diffs, PR bodies from branch logs, release notes, code review focus, issue templates, Actions debug, concept explainers.",
      "Invoke as MCP prompts with arguments — better than asking the model to freestyle format every time.",
    ],
    tryThis: [
      'git_commit_message(diff="…", context="fix login redirect")',
      'github_debug_workflow(workflow_name="ci", error_output="…", repo="o/r")',
    ],
  },
  {
    key: "non-interactive-git",
    category: "agents",
    title: "Non-interactive git for agents",
    subtitle: "Why MCP git must not open an editor or password prompt.",
    body: [
      "Child processes can't answer interactive prompts. We set GIT_TERMINAL_PROMPT=0 and SSH batch mode. Operations fail fast with JSON errors instead of hanging.",
      "Use credential manager or SSH remotes configured ahead of time. HTTPS without stored credentials will not work inside an agent loop.",
    ],
  },
  {
    key: "commit-messages",
    category: "git",
    title: "Commit messages that help reviewers",
    subtitle: "Conventional commits in one sentence of theory.",
    body: [
      "Format: `type(scope): imperative summary`. Types: feat, fix, docs, chore, ci, refactor, test. Body explains why when the diff isn't obvious.",
      "Good messages make Breakfast retro and release notes usable. Bad messages force everyone to read every line of diff.",
    ],
    tryThis: [
      "feat(web): add lecture tabs to help",
      "fix(digest): handle gh pr comments as list",
    ],
  },
  {
    key: "force-push",
    category: "git",
    title: "Force push",
    subtitle: "Rewrite remote history — only on branches you own.",
    body: [
      "After rebase or amend on a published branch, normal push rejects. `--force-with-lease` is safer than `--force`: it fails if someone else pushed meanwhile.",
      "MCP requires explicit `force=true` on push — never implied.",
    ],
    tryThis: ["git push --force-with-lease origin my-branch"],
    watchOut: ["Force pushing main/master is almost always wrong."],
  },
  {
    key: "release-tags",
    category: "github",
    title: "Releases and tags",
    subtitle: "Mark versions humans and package managers can find.",
    body: [
      "Tags are git refs; releases add notes and binaries on GitHub. Fleet `release_drift` compares local `pyproject` version to latest GitHub release tag.",
      "Align tag names with packaging (`v1.2.3` vs `1.2.3`) or drift checks false-positive.",
    ],
    tryThis: [
      'github_ops(operation="release_list", owner="…", repo="…")',
      'git_branch(operation="tag_create", tag_name="v1.0.0")',
    ],
  },
  {
    key: "ack-stale-prs",
    category: "fleet",
    title: "Acknowledging stale PRs",
    subtitle: "Politeness as maintenance — Breakfast drafts comments for you.",
    body: [
      'External contributor PRs that sit silent look abandoned. Maintainer ack ("thanks, we\'ll review this week" or "closing as superseded") resets expectations.',
      "`ack_drafts` suggests bodies; you still post via `pr_comment` or the GitHub UI.",
    ],
    tryThis: ['fleet_ops(operation="ack_drafts", stale_days=7)'],
  },
];

function LectureCard({ lecture }: { lecture: Lecture }) {
  return (
    <article className="rounded-xl border border-border bg-card/50 p-5 md:p-6 space-y-4">
      <header className="space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <BookOpen className="h-4 w-4 text-emerald-400 shrink-0" />
          <h2 className="text-lg font-semibold text-foreground">
            {lecture.title}
          </h2>
          <span className="text-[10px] font-mono uppercase tracking-wide text-muted-foreground ml-auto">
            {lecture.category}
          </span>
        </div>
        <p className="text-sm text-muted-foreground">{lecture.subtitle}</p>
      </header>

      <div className="text-[15px] leading-relaxed text-foreground/85 space-y-3">
        {lecture.body.map((para) => (
          <p key={para.slice(0, 40)}>{para}</p>
        ))}
      </div>

      {lecture.tryThis && lecture.tryThis.length > 0 && (
        <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-4 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-emerald-400 mb-2">
            Try this
          </p>
          <pre className="font-mono text-xs text-foreground/90 whitespace-pre-wrap leading-relaxed">
            {lecture.tryThis.join("\n")}
          </pre>
        </div>
      )}

      {lecture.watchOut && lecture.watchOut.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-amber-400/90">
            Watch out
          </p>
          <ul className="text-sm text-muted-foreground space-y-1.5 list-disc list-outside ml-4">
            {lecture.watchOut.map((w) => (
              <li key={w.slice(0, 50)}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </article>
  );
}

export function Lectures() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<LectureCategory>("all");
  const q = query.trim().toLowerCase();

  const filtered = useMemo(() => {
    return LECTURES.filter((l) => {
      if (category !== "all" && l.category !== category) return false;
      if (!q) return true;
      const hay =
        `${l.key} ${l.title} ${l.subtitle} ${l.body.join(" ")} ${(l.tryThis ?? []).join(" ")} ${(l.watchOut ?? []).join(" ")}`.toLowerCase();
      return hay.includes(q);
    });
  }, [q, category]);

  return (
    <div className="max-w-3xl space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Lectures</h1>
        <p className="text-sm mt-1 text-muted-foreground leading-relaxed">
          Bite-sized explanations for git, GitHub, fleet maintenance, and agent
          patterns — readable first, commands second. More in{" "}
          <Link to="/help" className="text-sky-400 hover:underline">
            Help
          </Link>{" "}
          for server architecture.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2 overflow-x-auto pb-1 border-b border-border/60">
        {CATEGORIES.map(({ id, label, Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => setCategory(id)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors border shrink-0 ${
              category === id
                ? "bg-emerald-500/15 text-emerald-200 border-emerald-500/35"
                : "bg-card/60 text-muted-foreground border-border hover:text-foreground"
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
            {id !== "all" && (
              <span className="text-[10px] opacity-70">
                ({LECTURES.filter((l) => l.category === id).length})
              </span>
            )}
          </button>
        ))}
      </div>

      <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg border border-border bg-card/40">
        <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
        <input
          className="flex-1 bg-transparent text-sm outline-none text-foreground placeholder:text-muted-foreground"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder='Search: "rebase", "dependabot", "gitingest", "breakfast"…'
        />
        <span className="text-xs text-muted-foreground shrink-0">
          {filtered.length} lectures
        </span>
      </div>

      <div className="space-y-5">
        {filtered.map((lecture) => (
          <LectureCard key={lecture.key} lecture={lecture} />
        ))}
        {filtered.length === 0 && (
          <p className="text-sm text-muted-foreground py-8 text-center">
            No match — try another category or a broader term like{" "}
            <span className="font-mono">merge</span> or{" "}
            <span className="font-mono">fleet</span>.
          </p>
        )}
      </div>
    </div>
  );
}
