import {
  AlertCircle,
  BookOpen,
  Boxes,
  Coffee,
  GitBranch,
  Github,
  HelpCircle,
  Layers,
  Monitor,
  Sparkles,
  Wrench,
} from "lucide-react";
import { type ReactNode, useState } from "react";
import { Link } from "react-router-dom";
import { useCapabilities } from "@/hooks/use-capabilities";

type HelpTab =
  | "whatisthis"
  | "architecture"
  | "tools"
  | "git"
  | "github"
  | "fleet"
  | "webapp"
  | "agents"
  | "troubleshoot";

const TABS: { id: HelpTab; label: string; Icon: typeof HelpCircle }[] = [
  { id: "whatisthis", label: "What is this", Icon: BookOpen },
  { id: "architecture", label: "Architecture", Icon: Layers },
  { id: "tools", label: "Tools", Icon: Wrench },
  { id: "git", label: "Git", Icon: GitBranch },
  { id: "github", label: "GitHub", Icon: Github },
  { id: "fleet", label: "Fleet", Icon: Coffee },
  { id: "webapp", label: "Web app", Icon: Monitor },
  { id: "agents", label: "Agents", Icon: Sparkles },
  { id: "troubleshoot", label: "Troubleshoot", Icon: AlertCircle },
];

function Code({ children }: { children: string }) {
  return (
    <code className="text-xs font-mono text-gh-green bg-black/25 px-1.5 py-0.5 rounded">
      {children}
    </code>
  );
}

function TryThis({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-lg border border-sky-500/25 bg-sky-500/5 px-4 py-3 text-sm text-foreground/90">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-sky-400 mb-1.5">
        Try this
      </p>
      {children}
    </div>
  );
}

function Lecture({
  title,
  subtitle,
  children,
  reference,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  reference?: ReactNode;
}) {
  return (
    <article className="rounded-xl border border-border bg-card/50 p-5 md:p-6 space-y-4">
      <header className="space-y-1">
        <h3 className="text-base font-semibold text-foreground tracking-tight">
          {title}
        </h3>
        {subtitle ? (
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        ) : null}
      </header>
      <div className="text-[15px] leading-relaxed text-foreground/85 space-y-3">
        {children}
      </div>
      {reference ? (
        <details className="group pt-1">
          <summary className="cursor-pointer text-xs font-medium text-muted-foreground hover:text-foreground list-none flex items-center gap-1">
            <span className="group-open:rotate-90 transition-transform inline-block">
              ▸
            </span>
            Reference detail
          </summary>
          <div className="mt-3 pl-4 border-l border-border/80 text-xs text-muted-foreground space-y-2 font-mono leading-relaxed">
            {reference}
          </div>
        </details>
      ) : null}
    </article>
  );
}

function LectureStack({ children }: { children: ReactNode }) {
  return <div className="space-y-5">{children}</div>;
}

export function HelpPage() {
  const [tab, setTab] = useState<HelpTab>("whatisthis");
  const { caps } = useCapabilities();
  const version = caps?.server?.version ?? "0.4.0";

  return (
    <div className="space-y-5 max-w-3xl">
      <div className="flex items-start gap-3">
        <HelpCircle className="h-8 w-8 shrink-0 text-sky-400 mt-1" />
        <div>
          <h1 className="text-2xl font-bold text-foreground">Help</h1>
          <p className="text-sm text-muted-foreground mt-1 leading-relaxed">
            How git-github-mcp fits together — written for humans. Concept
            deep-dives live on{" "}
            <Link to="/lectures" className="text-sky-400 hover:underline">
              Lectures
            </Link>
            . Version {version} · backend{" "}
            <strong className="text-foreground">10713</strong> · UI{" "}
            <strong className="text-foreground">10714</strong>.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 overflow-x-auto pb-1 border-b border-border/60">
        {TABS.map(({ id, label, Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => setTab(id)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors border shrink-0 ${
              tab === id
                ? "bg-sky-500/15 text-sky-200 border-sky-500/35"
                : "bg-card/60 text-muted-foreground border-border hover:text-foreground"
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {tab === "whatisthis" && (
        <LectureStack>
          <Lecture
            title="What problem does this solve?"
            subtitle="One sentence: your AI (and you) get reliable Git and GitHub without fighting the shell."
          >
            <p>
              Agents love to run <Code>git status</Code> and open pull requests
              — until PATH is wrong, <Code>gh</Code> isn&apos;t logged in, or a
              tool list has ninety entries and the model picks the wrong one.
              This server wraps the real CLIs behind a <em>small</em> set of MCP
              tools with predictable JSON responses.
            </p>
            <p>
              It also knows about the <strong>sandraschi MCP fleet</strong>: a
              daily &quot;breakfast&quot; pass that scans repos for stale PRs,
              CI failures, Dependabot noise, and registry drift. Think
              maintainer inbox, not just raw git commands.
            </p>
          </Lecture>

          <Lecture
            title="Your first ten minutes"
            subtitle="No theory — just get something working."
          >
            <ol className="list-decimal list-outside ml-5 space-y-2">
              <li>
                Install GitHub CLI and sign in: <Code>gh auth login</Code>.
              </li>
              <li>
                Double-click <Code>web\start.bat</Code> (or the fleet launcher
                in <Code>mcp-central-docs\starts\</Code>).
              </li>
              <li>
                Open{" "}
                <Link to="/breakfast" className="text-sky-400 hover:underline">
                  Breakfast
                </Link>{" "}
                and run a <em>short</em> fleet list first (two repos, registry
                unchecked) before the full ~140-repo scan.
              </li>
              <li>
                Glance at{" "}
                <Link to="/inbox" className="text-sky-400 hover:underline">
                  Inbox
                </Link>{" "}
                for open PRs on those repos.
              </li>
            </ol>
            <TryThis>
              <p className="mb-2">
                Smoke-test GitHub from the Tools page or chat:
              </p>
              <p>
                <Code>github_ops(operation=&quot;auth_status&quot;)</Code>
              </p>
            </TryThis>
          </Lecture>

          <Lecture title="Who is this for?">
            <p>
              <strong>Maintainers</strong> of many GitHub repos who want a
              morning digest and a web dashboard, not another bookmark folder of
              Actions tabs.
            </p>
            <p>
              <strong>Agent builders</strong> wiring Claude Desktop, Cursor, or
              a supervisor bot that must commit, push, and comment on PRs
              without hanging on interactive prompts.
            </p>
            <p>
              <strong>You, locally</strong> — the web UI is the same backend the
              MCP client uses; nothing is &quot;agent-only.&quot;
            </p>
          </Lecture>

          <Lecture title="What you need installed">
            <p>
              Python 3.12+ and <Code>uv</Code> (the launcher syncs deps). Git
              for Windows. Node for the Vite UI.
            </p>
            <p>
              <Code>gh</Code> must be authenticated — almost every GitHub and
              fleet feature depends on it. No API token wiring in the server; we
              delegate to the CLI you already use.
            </p>
          </Lecture>
        </LectureStack>
      )}

      {tab === "architecture" && (
        <LectureStack>
          <Lecture
            title="Three doors into the same house"
            subtitle="stdio for Claude, HTTP for the web, MCPB for drag-and-drop install."
          >
            <p>
              At the center is one FastMCP server.{" "}
              <strong>Claude Desktop</strong> talks over stdio (or an{" "}
              <Code>.mcpb</Code> bundle). <strong>This web app</strong> talks to
              a FastAPI bridge on port 10713; Vite on 10714 proxies{" "}
              <Code>/api</Code> so the browser never hard-codes cross-origin
              URLs.
            </p>
            <p>
              Optional <Code>MCP_TRANSPORT=http</Code> exposes streamable MCP at{" "}
              <Code>/mcp</Code> for remote clients. Day to day you rarely need
              it if you use stdio or the web UI.
            </p>
          </Lecture>

          <Lecture title="What happens when you click Start full suite">
            <p>
              Breakfast doesn&apos;t fire one giant API call. The server walks
              the fleet <em>step by step</em> — morning digest repo by repo,
              then CI, Dependabot, workspace checks, and so on. Progress streams
              back as NDJSON; the heavy result lands in a cache you fetch when
              the bar hits 100%.
            </p>
            <p>
              A full registry run can take ten minutes. That&apos;s normal:
              it&apos;s doing real <Code>gh</Code> work per repo, not pretending
              instant magic.
            </p>
            <TryThis>
              <p>
                MCP equivalent:{" "}
                <Code>fleet_ops(operation=&quot;full_suite&quot;)</Code>
              </p>
            </TryThis>
          </Lecture>

          <Lecture
            title="Portmanteau tools — why not 100 MCP tools?"
            reference={
              <p>
                git_core · git_branch · git_admin · git_blame · github_ops ·
                fleet_morning_digest · fleet_ops · git_github_status ·
                git_github_help · git_agentic_workflow ·
                git_github_search_workflow
              </p>
            }
          >
            <p>
              MCP clients choked on enormous tool lists. We group operations:
              one tool called <Code>github_ops</Code>, you pass{" "}
              <Code>operation=&quot;pr_list&quot;</Code>. Same pattern for git (
              <Code>git_core</Code>, <Code>git_branch</Code>,{" "}
              <Code>git_admin</Code>) and fleet (<Code>fleet_ops</Code>).
            </p>
            <p>
              Errors return JSON with <Code>success: false</Code> and hints —
              they don&apos;t throw across the wire.
            </p>
          </Lecture>

          <Lecture
            title="HTTP map (when you’re debugging)"
            reference={
              <>
                <p>
                  GET /health · /api/capabilities · /api/logs ·
                  /api/fleet-suite/last
                </p>
                <p>
                  POST /api/git · /api/github · /api/fleet-ops ·
                  /api/fleet-suite/stream
                </p>
              </>
            }
          >
            <p>
              If the UI says &quot;backend unreachable,&quot; port 10713
              isn&apos;t up — restart <Code>web\start.bat</Code>. If Breakfast
              hangs at 100%, check the stream finished and{" "}
              <Code>/api/fleet-suite/last</Code> returns JSON (circular refs in
              council payload were a past bug — fixed).
            </p>
          </Lecture>
        </LectureStack>
      )}

      {tab === "tools" && (
        <LectureStack>
          <Lecture title="How to read a tool call">
            <p>
              Every portmanteau tool wants an <Code>operation</Code> string plus
              optional fields. Always check
            </p>
            <p>
              <Code>response.success</Code> before using{" "}
              <Code>response.result</Code>. On failure, read <Code>error</Code>{" "}
              and <Code>recovery_options</Code> — they’re written for the model{" "}
              <em>and</em> for you.
            </p>
          </Lecture>

          <Lecture title="Git tools — pick the right drawer">
            <p>
              <strong>git_core</strong> — everyday work: status, log, add,
              commit, push, pull, clone.
            </p>
            <p>
              <strong>git_branch</strong> — branches, merge, rebase, stash,
              tags.
            </p>
            <p>
              <strong>git_admin</strong> — remotes, reset, revert, submodules,
              bisect, worktrees. The &quot;handle with care&quot; drawer.
            </p>
            <p>
              <strong>git_blame</strong> — one file, one question: who wrote
              this line?
            </p>
          </Lecture>

          <Lecture title="GitHub — one tool, the whole platform">
            <p>
              <Code>github_ops</Code> wraps <Code>gh</Code>: repos, issues, PRs,
              releases, Actions, search, Projects, Packages, Gitingest URLs. If
              you can do it in gh, we probably exposed it as an operation.
            </p>
            <TryThis>
              <p>List open PRs on a repo:</p>
              <p>
                <Code>
                  github_ops(operation=&quot;pr_list&quot;,
                  owner=&quot;sandraschi&quot;, repo=&quot;git-github-mcp&quot;)
                </Code>
              </p>
            </TryThis>
          </Lecture>

          <Lecture title="Fleet tools — maintainer mode">
            <p>
              <strong>fleet_morning_digest</strong> — scan fleet lines for open
              PRs/issues, stale threads, notifications; optionally write{" "}
              <Code>morning-digest.md</Code> or push to aiwatcher.
            </p>
            <p>
              <strong>fleet_ops</strong> — sixteen ops; <Code>full_suite</Code>{" "}
              runs all of them in order. Use single ops when you only need CI
              pulse or port audit.
            </p>
          </Lecture>

          <Lecture
            title="Prompts and agentic workflows"
            reference={
              <p>
                Prompts: git_commit_message, git_release_notes,
                git_pr_description, git_review_diff, github_issue_template,
                github_debug_workflow, git_github_explain_concept
              </p>
            }
          >
            <p>
              Seven MCP <em>prompts</em> help models draft commit messages, PR
              bodies, release notes, and debug failing workflows — with
              structured argument slots.
            </p>
            <p>
              <Code>git_agentic_workflow</Code> and{" "}
              <Code>git_github_search_workflow</Code> need a client that
              supports <strong>MCP sampling</strong>: the server asks the host
              LLM to plan steps, then executes them. Cursor and
              Antigravity-class clients shine here; plain HTTP bridge uses
              simpler presets instead.
            </p>
          </Lecture>
        </LectureStack>
      )}

      {tab === "git" && (
        <LectureStack>
          <Lecture title="Local git without surprise prompts">
            <p>
              MCP runs non-interactive child processes. We set{" "}
              <Code>GIT_TERMINAL_PROMPT=0</Code> so git never blocks waiting for
              a password or merge message you can’t see. If an operation needs
              input, it fails clearly in JSON instead of hanging forever.
            </p>
          </Lecture>

          <Lecture title="A sane commit–push loop">
            <p>
              Most agent tasks follow the same story: see state, stage, commit,
              push.
            </p>
            <TryThis>
              <ol className="list-decimal list-outside ml-5 space-y-1 text-sm">
                <li>
                  <Code>
                    git_core(operation=&quot;status&quot;,
                    repo_path=&quot;…&quot;)
                  </Code>
                </li>
                <li>
                  <Code>
                    git_core(operation=&quot;add&quot;, all_files=true)
                  </Code>
                </li>
                <li>
                  <Code>
                    git_core(operation=&quot;commit&quot;, message=&quot;fix:
                    …&quot;)
                  </Code>
                </li>
                <li>
                  <Code>
                    git_core(operation=&quot;push&quot;, set_upstream=true)
                  </Code>{" "}
                  on first push of a branch
                </li>
              </ol>
            </TryThis>
            <p>
              <Code>status</Code> is &quot;high fidelity&quot;: staged,
              unstaged, untracked, and unmerged counts — useful for agents
              deciding what to do next.
            </p>
          </Lecture>

          <Lecture title="Branches, stash, and tags">
            <p>
              Feature work lives in <Code>git_branch</Code>: create/switch
              branches, merge, rebase, stash WIP, tag releases. Prefer explicit
              branch names in tool args - don't assume <Code>main</Code> vs{" "}
              <Code>master</Code>.
            </p>
          </Lecture>

          <Lecture title="Blame - who wrote this line?">
            <p>
              <Code>git_blame</Code> annotates a file line-by-line showing the
              commit hash, author, and date for each line. It does not assign
              moral responsibility - it answers "which commit last touched this
              line, and who authored it?" Useful when reviewing unfamiliar code:
              pick a suspicious line, blame it, then inspect the linked commit
              for context.
            </p>
            <TryThis>
              <p>
                <Code>git_blame(file_path="src/server.py")</Code>
              </p>
            </TryThis>
          </Lecture>

          <Lecture title="Merge vs rebase - two ways to integrate">
            <p>
              <Code>merge</Code> creates a new commit that joins two branch
              histories. It preserves exactly what happened and when - the
              record is truthful but the graph can tangle fast with many
              contributors.
            </p>
            <p>
              <Code>rebase</Code> rewrites your branch as if it started from the
              latest <Code>main</Code>. The history reads linearly and cleanly,
              but every rebased commit gets a new hash - never rebase a branch
              others have already pulled from. The server passes{" "}
              <Code>--rebase-merges</Code> by default so merge commits from
              sub-branch merges are preserved.
            </p>
            <p>
              <strong>Rule of thumb:</strong> rebase local cleanup branches,
              merge shared feature branches.
            </p>
          </Lecture>

          <Lecture title="Cherry-pick - take one commit, not the whole branch">
            <p>
              <Code>cherry_pick</Code> copies a single commit from one branch
              onto your current branch. Unlike merge (which brings everything)
              or rebase (which replays a whole series), cherry-pick targets
              exactly one fix. Common uses: backport a hotfix to a release
              branch, or grab a bugfix from a sibling branch without merging its
              incomplete features.
            </p>
            <TryThis>
              <p>
                <Code>
                  git_admin(operation="cherry_pick", commit="a1b2c3d")
                </Code>
              </p>
            </TryThis>
          </Lecture>

          <Lecture title="Force push - when and (mostly) when not">
            <p>
              Normal <Code>push</Code> refuses if your branch is behind the
              remote. <Code>push --force</Code>
              overwrites the remote branch with your local state. Use it only on{" "}
              <strong>personal branches</strong>
              you haven't shared - typically after rebasing a PR branch. Never
              force-push to <Code>main</Code>,<Code>master</Code>, or any branch
              others collaborate on: you will delete their commits.
            </p>
            <p>
              The server requires <Code>force=True</Code> to allow force push -
              it will never happen by accident.
            </p>
          </Lecture>

          <Lecture title="When things go wrong - admin tools">
            <p>
              <Code>git_admin</Code> holds reset, revert, cherry-pick, clean,
              submodule, bisect, worktree.
            </p>
            <p>
              <Code>reset</Code> moves the current branch pointer backwards,
              optionally discarding worktree changes (<Code>mode="hard"</Code>).{" "}
              <Code>revert</Code> creates a new commit that undoes a previous
              one - safer for shared branches because it doesn't rewrite
              history.
            </p>
            <p>
              Destructive modes (<Code>reset mode="hard"</Code>,{" "}
              <Code>clean -fd</Code>, force push) require you to pass explicit
              force flags - never silently.
            </p>
          </Lecture>

          <Lecture title="Reset, revert, clean - undoing work">
            <p>
              <Code>reset</Code> moves the branch pointer.{" "}
              <Code>mode="soft"</Code> keeps your changes staged;{" "}
              <Code>mode="mixed"</Code> (default) unstages them;{" "}
              <Code>mode="hard"</Code>
              discards everything. There is no undo for hard reset - consider{" "}
              <Code>revert</Code> instead when the commit is already pushed.
            </p>
            <p>
              <Code>clean</Code> removes untracked files from the working tree.
              Use <Code>dry_run=True</Code>
              first to see what would be deleted.
            </p>
          </Lecture>
        </LectureStack>
      )}

      {tab === "github" && (
        <LectureStack>
          <Lecture title="Everything goes through gh">
            <p>
              We don&apos;t embed a separate GitHub SDK. Your machine&apos;s{" "}
              <Code>gh auth login</Code> session is the source of truth. Token
              scopes and org access are whatever gh already has — which keeps
              behavior identical to what you get in the terminal.
            </p>
            <TryThis>
              <p>
                <Code>git_github_status</Code> or{" "}
                <Code>github_ops(operation=&quot;auth_status&quot;)</Code>
              </p>
            </TryThis>
          </Lecture>

          <Lecture title="Triage open PRs and issues">
            <p>
              For a single repo, <Code>pr_list</Code> and{" "}
              <Code>issue_list</Code> are the workhorses. The web{" "}
              <Link to="/inbox" className="text-sky-400 hover:underline">
                Inbox
              </Link>{" "}
              runs the same calls across many <Code>owner/repo</Code> lines —
              paste a fleet list or load from registry.
            </p>
            <p>
              Stale detection (no comments, quiet for N days) powers Breakfast
              and ack-draft suggestions — it skips PRs you opened yourself as
              maintainer.
            </p>
          </Lecture>

          <Lecture title="CI and Actions — success and failed together">
            <p>
              <Code>workflow_runs</Code> pulls the last 20 runs per repo; fleet{" "}
              <Code>ci_pulse</Code> scans the whole fleet. The web{" "}
              <Link to="/ci" className="text-sky-400 hover:underline">
                CI Monitor
              </Link>{" "}
              now shows <strong>success and failed side by side</strong>: 5
              tiles (Success/Failed/Cancelled/In progress/Total) plus success
              rate, <Code>Failed only</Code> toggle, log tail, and buttons to{" "}
              <Code>Trigger ci.yml</Code> or <Code>Rerun failed</Code>.
            </p>
            <p>
              Fix loop: red tile → open run → read log tail →{" "}
              <Code>just ci</Code> locally (ruff/pytest/tsc) → push → trigger
              here. GitHub notification emails stop when the bar goes green.
            </p>
            <TryThis>
              <p>
                When a workflow breaks, feed its error slice to{" "}
                <Code>github_debug_workflow</Code> or click{" "}
                <Code>AI Diagnose</Code> on the CI page.
              </p>
            </TryThis>
          </Lecture>

          <Lecture title="Stars — received vs given">
            <p>
              <Code>stars_summary</Code> sums <Code>stargazers_count</Code>{" "}
              across your public repos (received stars). GitHub profile{" "}
              <Code>?tab=stars</Code> is <em>given</em> — different number.{" "}
              <Code>stars_history</Code> buckets <Code>starred_at</Code> for the
              amber/sky trajectory on{" "}
              <Link to="/stars" className="text-sky-400 hover:underline">
                Stars
              </Link>
              .
            </p>
          </Lecture>

          <Lecture title="Search, topics, and Gitingest">
            <p>
              <Code>search_repos</Code>, <Code>search_code</Code>, and{" "}
              <Code>code_find_repos</Code> help agents discover repos (e.g. find
              stray <Code>.bak</Code> files). <Code>gitingest_url</Code> turns a
              GitHub URL into an ingest link for stuffing repo context into
              another tool — hub → ingest, one rule of thumb.
            </p>
          </Lecture>

          <Lecture title="Releases, labels, secrets — the long tail">
            <p>
              Releases, collaborators, labels, org projects, packages — all live
              under <Code>github_ops</Code>. You won’t need them daily, but
              they’re there so agents don&apos;t fall back to shell escapes. See
              reference for the full operation list.
            </p>
          </Lecture>
        </LectureStack>
      )}

      {tab === "fleet" && (
        <LectureStack>
          <Lecture
            title="What is breakfast?"
            subtitle="A maintainer morning ritual for 100+ MCP repos — not a cron inside this server."
          >
            <p>
              MCP has no built-in scheduler. Breakfast is the <em>payload</em> a
              human or supervisor agent runs daily: what needs eyes today? The
              web runner, MCP tools, and optional Windows scheduled task all
              call the same digest code.
            </p>
            <p>
              Output: counts of notifications, stale PRs, CI failures,
              Dependabot alerts, dirty local clones, port collisions, docs-gate
              gaps — plus structured JSON for robofang-style supervisors (
              <Code>council_payload</Code>).
            </p>
          </Lecture>

          <Lecture title="Fleet list vs registry">
            <p>
              <strong>Fleet text box</strong> — one <Code>owner/repo</Code> per
              line; good for a focused pass on two or ten repos.
            </p>
            <p>
              <strong>Registry checkbox</strong> — loads the full list from
              mcp-central-docs (~140 repos). Powerful, slow; uncheck when
              debugging.
            </p>
            <p>
              Shared format with{" "}
              <Link to="/inbox" className="text-sky-400 hover:underline">
                Inbox
              </Link>
              ; localStorage keeps your last list.
            </p>
          </Lecture>

          <Lecture title="The sixteen fleet_ops — in plain English">
            <ul className="space-y-2 list-none">
              <li>
                <strong>registry_load</strong> — read fleet registry JSON
              </li>
              <li>
                <strong>port_audit</strong> — collisions in WEBAPP_PORTS vs
                registry
              </li>
              <li>
                <strong>docs_gate</strong> — required docs present per repo
              </li>
              <li>
                <strong>quarantine_report</strong> — deprecated/quarantined
                entries
              </li>
              <li>
                <strong>ci_pulse</strong> — recent workflow failures
              </li>
              <li>
                <strong>dependabot_digest</strong> — open security alerts
              </li>
              <li>
                <strong>mention_inbox</strong> — @mentions since last run
              </li>
              <li>
                <strong>ack_drafts</strong> — suggested comments on stale PRs
              </li>
              <li>
                <strong>local_dirty</strong> — uncommitted work in clone paths
              </li>
              <li>
                <strong>release_drift</strong> — pyproject version vs latest
                GitHub release
              </li>
              <li>
                <strong>grade_snapshot</strong> — scraper-mcp quality matrix
              </li>
              <li>
                <strong>gitingest_bundle</strong> — ingest URLs for fleet repos
              </li>
              <li>
                <strong>runner_status</strong> — last digest time, scheduled
                task
              </li>
              <li>
                <strong>weekly_retro</strong> — merged PRs and new issues (7d)
              </li>
              <li>
                <strong>council_payload</strong> — summary for supervisor agents
              </li>
              <li>
                <strong>full_suite</strong> — all of the above, in order
              </li>
            </ul>
          </Lecture>

          <Lecture title="Delivery options">
            <p>
              Check <strong>Write markdown file</strong> to save{" "}
              <Code>morning-digest.md</Code> under server state.
              <strong> Push to aiwatcher</strong> when your ingest endpoint is
              configured. <strong>Notifications since last run</strong> avoids
              re-reading ancient GitHub notifications.
            </p>
            <TryThis>
              <p>
                Schedule on Windows:{" "}
                <Code>scripts\install_morning_task.ps1</Code>
              </p>
            </TryThis>
          </Lecture>
        </LectureStack>
      )}

      {tab === "webapp" && (
        <LectureStack>
          <Lecture title="Why a web UI at all?">
            <p>
              Agents get MCP; humans get a dashboard. Same backend — you can
              verify what the agent saw, run a fleet suite with a progress bar,
              and read logs when something fails silently in the IDE.
            </p>
          </Lecture>

          <Lecture title="Page guide">
            <ul className="space-y-3">
              <li>
                <Link
                  to="/breakfast"
                  className="text-sky-400 hover:underline font-medium"
                >
                  Breakfast
                </Link>{" "}
                — full maintainer suite, tabs for CI, security, retro, etc.
              </li>
              <li>
                <Link
                  to="/inbox"
                  className="text-sky-400 hover:underline font-medium"
                >
                  Inbox
                </Link>{" "}
                — PRs and issues across fleet lines; stale highlights
              </li>
              <li>
                <Link
                  to="/prs"
                  className="text-sky-400 hover:underline font-medium"
                >
                  Pull requests
                </Link>{" "}
                / Issues / Repos — single-repo views
              </li>
              <li>
                <Link
                  to="/tools"
                  className="text-sky-400 hover:underline font-medium"
                >
                  Tools
                </Link>{" "}
                — invoke MCP tools over HTTP
              </li>
              <li>
                <Link
                  to="/logs"
                  className="text-sky-400 hover:underline font-medium"
                >
                  Logs
                </Link>{" "}
                — ring buffer of API activity
              </li>
              <li>
                <Link
                  to="/apps"
                  className="text-sky-400 hover:underline font-medium"
                >
                  Apps
                </Link>{" "}
                — fleet webapp catalog
              </li>
              <li>
                <Link
                  to="/dashboard"
                  className="text-sky-400 hover:underline font-medium"
                >
                  Dashboard
                </Link>{" "}
                — hero + 6 KPIs, stars glance, quick actions
              </li>
              <li>
                <Link
                  to="/stars"
                  className="text-sky-400 hover:underline font-medium"
                >
                  Stars
                </Link>{" "}
                — received stars, leaderboard, trajectory
              </li>
              <li>
                <Link
                  to="/ci"
                  className="text-sky-400 hover:underline font-medium"
                >
                  CI Monitor
                </Link>{" "}
                — success + failed stats, last 20 runs, rerun/trigger, AI
                diagnose (how to fix broken CI)
              </li>
              <li>
                <Link
                  to="/discovery"
                  className="text-sky-400 hover:underline font-medium"
                >
                  Discovery
                </Link>{" "}
                — 5 presets: org snapshot, topic hunt, code sweep, repo deep
                dive, global search
              </li>
              <li>
                <Link
                  to="/chat"
                  className="text-sky-400 hover:underline font-medium"
                >
                  Chat
                </Link>{" "}
                — single-column shortcut shell, dropdown examples
              </li>
            </ul>
          </Lecture>

          <Lecture title="Starting and stopping">
            <p>
              <Code>web\start.bat</Code> kills zombie processes on 10713/10714,
              syncs Python deps, opens backend + Vite, waits for health, then
              opens the browser. Closing the launcher windows stops the stack.
            </p>
          </Lecture>
        </LectureStack>
      )}

      {tab === "agents" && (
        <LectureStack>
          <Lecture title="Claude Desktop (MCPB)">
            <p>
              Build or download <Code>dist\git-github-mcp-v*.mcpb</Code>, drag
              onto Claude Desktop, accept install. The bundle uses{" "}
              <Code>uv run</Code> from the extension directory — you still need
              uv and gh on the machine.
            </p>
            <TryThis>
              <p>
                Rebuild bundle: <Code>.\mcpb\pack.ps1</Code> or{" "}
                <Code>just mcpb-pack</Code>
              </p>
            </TryThis>
          </Lecture>

          <Lecture title="Cursor and other MCP hosts">
            <p>
              Point the host at <Code>uv run git-github-mcp</Code> from the repo
              (stdio). HTTP bridge on 10713 is optional unless the client only
              speaks streamable HTTP.
            </p>
            <p>
              Use <Code>git_github_help</Code> with{" "}
              <Code>level=intermediate</Code> when the model needs parameter
              tables without loading this page.
            </p>
          </Lecture>

          <Lecture title="Supervisor heartbeat pattern">
            <p>
              A daily agent (OpenClaw, robofang, etc.) should call{" "}
              <Code>fleet_ops(full_suite)</Code> or at minimum{" "}
              <Code>fleet_morning_digest</Code>, then act on{" "}
              <Code>council_payload.summary</Code>. This web app is the human
              mirror of that heartbeat — same data, different skin.
            </p>
            <p>
              Fleet doc: mcp-central-docs{" "}
              <Code>patterns/GITHUB_MAINTAINER_HEARTBEAT.md</Code>.
            </p>
          </Lecture>

          <Lecture title="When to use sampling workflows">
            <p>
              Open-ended &quot;find all repos with X and open issues&quot; →{" "}
              <Code>git_github_search_workflow</Code>. Multi-step &quot;create
              branch, commit, push, open PR&quot; →{" "}
              <Code>git_agentic_workflow</Code>. Without sampling, use the web
              discovery presets or chain <Code>github_ops</Code> yourself.
            </p>
          </Lecture>
        </LectureStack>
      )}

      {tab === "troubleshoot" && (
        <LectureStack>
          <Lecture title="Failed to fetch / backend unreachable">
            <p>
              Port 10713 isn&apos;t listening. Run <Code>web\start.bat</Code>{" "}
              and wait for &quot;backend ready&quot;. Don&apos;t call{" "}
              <Code>localhost:10713</Code> from the UI manually — let Vite proxy{" "}
              <Code>/api</Code>.
            </p>
          </Lecture>

          <Lecture title="gh auth errors">
            <p>
              Run <Code>gh auth login</Code> and <Code>gh auth status</Code> in
              a normal terminal. Fleet suite &quot;succeeds&quot; partially but
              GitHub steps empty when gh isn&apos;t logged in.
            </p>
          </Lecture>

          <Lecture title="Breakfast spinner stuck at 100%">
            <p>
              Fixed in recent builds: stream sends a lightweight done ack; full
              JSON loads from <Code>/api/fleet-suite/last</Code>. Restart
              backend after pulling. Hard-refresh the browser.
            </p>
          </Lecture>

          <Lecture title="Full suite takes forever">
            <p>
              ~140 repos × several gh calls each ≈ ten minutes. Use a short
              fleet list or disable registry for dev. Watch the progress bar —
              repo name and step should advance.
            </p>
          </Lecture>

          <Lecture title="npm / Vite won&apos;t start">
            <p>
              Launcher resolves <Code>npm.cmd</Code> on Windows (not{" "}
              <Code>npm.ps1</Code>). If Vite still fails, run{" "}
              <Code>cd web</Code> then <Code>npm install</Code> once, then
              restart <Code>start.bat</Code>.
            </p>
          </Lecture>

          <Lecture title="Git hangs or asks for credentials">
            <p>
              Use SSH or credential manager outside MCP; the server forces
              non-interactive git. HTTPS repos needing password prompt will fail
              fast — switch to SSH remote or gh credential helper.
            </p>
          </Lecture>
        </LectureStack>
      )}

      <div className="flex items-center gap-2 text-xs text-muted-foreground pt-2">
        <Boxes className="h-3.5 w-3.5" />
        <a
          href="https://github.com/sandraschi/mcp-central-docs"
          className="text-sky-400 hover:underline"
          target="_blank"
          rel="noopener noreferrer"
        >
          mcp-central-docs
        </a>
        · fleet standards &amp; maintainer heartbeat
      </div>
    </div>
  );
}
