import {
  Bell,
  CircleDot,
  Coffee,
  Database,
  ExternalLink,
  GitPullRequest,
  Loader2,
  Play,
  RefreshCw,
  Shield,
  Workflow,
} from "lucide-react";
import {
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  type FleetSuiteProgress,
  runFleetOps,
  runFleetSuiteStream,
} from "@/lib/api";

const FLEET_KEY = "git-github-mcp-inbox-fleet";
const LAST_SUITE_KEY = "git-github-mcp-breakfast-suite";

type RunnerStatus = "idle" | "running" | "done" | "error";

type FleetOp<T = unknown> = {
  success?: boolean;
  result?: T;
  error?: string;
  message?: string;
};

type Author = { login?: string };

type DigestPr = {
  number: number;
  title: string;
  state: string;
  url: string;
  author?: Author;
  isDraft?: boolean;
  createdAt: string;
  updatedAt?: string;
  comments?: number;
  repo_slug: string;
  repo_url: string;
  is_stale?: boolean;
  stale_reason?: string;
};

type DigestIssue = {
  number: number;
  title: string;
  state: string;
  url: string;
  author?: Author;
  createdAt: string;
  updatedAt?: string;
  repo_slug: string;
  repo_url: string;
  is_stale?: boolean;
  stale_reason?: string;
};

type NotificationRow = {
  title?: string;
  reason?: string;
  updated_at?: string;
  unread?: boolean;
  subject_title?: string;
  subject_url?: string;
  repository?: string;
  error?: string;
};

type RepoLink = {
  slug: string;
  url: string;
  open_prs: number;
  open_issues: number;
};

type DigestResult = {
  generated_at?: string;
  maintainer?: string;
  stale_days?: number;
  since_last_run?: string | null;
  totals?: {
    open_prs: number;
    open_issues: number;
    stale_prs: number;
    stale_issues: number;
    notifications: number;
  };
  repo_links?: RepoLink[];
  open_prs?: DigestPr[];
  open_issues?: DigestIssue[];
  notifications?: NotificationRow[];
  repo_errors?: string[];
  delivery?: Record<string, unknown>;
};

type SuiteResult = {
  generated_at?: string;
  morning_digest?: FleetOp<DigestResult>;
  registry_load?: FleetOp<{
    fleet_repos_text?: string;
    github_repos?: string[];
    entry_count?: number;
  }>;
  ci_pulse?: FleetOp<{
    failure_count?: number;
    failures?: Record<string, unknown>[];
  }>;
  dependabot_digest?: FleetOp<{
    alert_count?: number;
    alerts?: Record<string, unknown>[];
  }>;
  ack_drafts?: FleetOp<{ count?: number; drafts?: Record<string, unknown>[] }>;
  port_audit?: FleetOp<{
    collision_count?: number;
    mismatch_count?: number;
    collisions?: Record<string, unknown>[];
    mismatches?: Record<string, unknown>[];
  }>;
  docs_gate?: FleetOp<{
    non_compliant_count?: number;
    non_compliant?: Record<string, unknown>[];
  }>;
  quarantine_report?: FleetOp<{
    count?: number;
    repos?: Record<string, unknown>[];
  }>;
  local_dirty?: FleetOp<{
    dirty_count?: number;
    sync_drift_count?: number;
    dirty?: Record<string, unknown>[];
    sync_drift?: Record<string, unknown>[];
  }>;
  release_drift?: FleetOp<{
    drift_count?: number;
    drifts?: Record<string, unknown>[];
  }>;
  grade_snapshot?: FleetOp<{
    ok?: boolean;
    matrix?: unknown;
    error?: string;
    recovery_options?: string[];
  }>;
  gitingest_bundle?: FleetOp<{
    links?: { repo_slug: string; gitingest_url: string }[];
  }>;
  runner_status?: FleetOp<{
    last_run_at?: string;
    scheduled_task?: { installed?: boolean };
  }>;
  weekly_retro?: FleetOp<{
    merged_pr_count?: number;
    new_issue_count?: number;
    merged_prs?: Record<string, unknown>[];
    new_issues?: Record<string, unknown>[];
  }>;
  council_payload?: FleetOp<{
    summary?: Record<string, number>;
    actions?: string[];
  }>;
};

type SuiteResponse = FleetOp<SuiteResult>;

type TabId =
  | "overview"
  | "notifications"
  | "prs"
  | "issues"
  | "repos"
  | "ci"
  | "security"
  | "acks"
  | "catalog"
  | "workspace"
  | "links"
  | "retro";

function unwrap<T>(op?: FleetOp<T>): T | null {
  if (!op?.success) return null;
  return (op.result ?? null) as T | null;
}

function parseFleet(text: string): string {
  return text
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l && !l.startsWith("#"))
    .join("\n");
}

function relTime(iso: string | undefined): string {
  if (!iso) return "";
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "";
  const days = Math.floor((Date.now() - t) / 86400000);
  if (days === 0) return "today";
  if (days === 1) return "1d ago";
  return `${days}d ago`;
}

function loadCachedSuite(): SuiteResult | null {
  try {
    const raw = localStorage.getItem(LAST_SUITE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as SuiteResult;
  } catch {
    return null;
  }
}

export function BreakfastPage() {
  const [fleetText, setFleetText] = useState(() => {
    try {
      return localStorage.getItem(FLEET_KEY) ?? "";
    } catch {
      return "sandraschi/git-github-mcp";
    }
  });
  const [useRegistry, setUseRegistry] = useState(true);
  const [staleDays, setStaleDays] = useState(7);
  const [sinceLastRun, setSinceLastRun] = useState(true);
  const [deliverFile, setDeliverFile] = useState(true);
  const [deliverAiwatcher, setDeliverAiwatcher] = useState(false);
  const [tab, setTab] = useState<TabId>("overview");
  const [suite, setSuite] = useState<SuiteResult | null>(() =>
    loadCachedSuite(),
  );
  const [status, setStatus] = useState<RunnerStatus>(() =>
    loadCachedSuite() ? "done" : "idle",
  );
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [registryLoading, setRegistryLoading] = useState(false);
  const [progress, setProgress] = useState<FleetSuiteProgress | null>(null);

  const data = useMemo(() => unwrap(suite?.morning_digest), [suite]);

  const loadRegistry = useCallback(async () => {
    setRegistryLoading(true);
    setError(null);
    try {
      const res = (await runFleetOps("registry_load", {})) as FleetOp<{
        fleet_repos_text?: string;
      }>;
      if (!res.success) throw new Error(res.error ?? "registry_load failed");
      const text = res.result?.fleet_repos_text;
      if (text) {
        setFleetText(text);
        setUseRegistry(true);
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setRegistryLoading(false);
    }
  }, []);

  const run = useCallback(async () => {
    const fleet = parseFleet(fleetText);
    if (!useRegistry && !fleet) {
      setError("Add at least one owner/repo line, or enable fleet registry.");
      setStatus("error");
      return;
    }
    setStatus("running");
    setError(null);
    setLastMessage(null);
    setProgress(null);
    try {
      const deliverParts: string[] = [];
      if (deliverFile) deliverParts.push("file");
      if (deliverAiwatcher) deliverParts.push("aiwatcher");

      const res = (await runFleetSuiteStream(
        {
          fleet_repos: fleet || undefined,
          use_registry: useRegistry,
          stale_days: staleDays,
          since_last_run: sinceLastRun,
          deliver: deliverParts.length > 0 ? deliverParts.join(",") : undefined,
        },
        (p) => setProgress(p),
      )) as SuiteResponse;
      if (!res.success) throw new Error(res.error ?? "Fleet suite failed");
      const result = res.result ?? null;
      setProgress(null);
      setSuite(result);
      setLastMessage(res.message ?? "Full fleet suite finished");
      setStatus("done");
      if (result) {
        try {
          localStorage.setItem(LAST_SUITE_KEY, JSON.stringify(result));
        } catch {
          /* ignore */
        }
      }
    } catch (e) {
      setError(String(e));
      setStatus("error");
      setProgress(null);
    }
  }, [
    fleetText,
    useRegistry,
    staleDays,
    sinceLastRun,
    deliverFile,
    deliverAiwatcher,
  ]);

  useEffect(() => {
    try {
      localStorage.setItem(FLEET_KEY, fleetText);
    } catch {
      /* ignore */
    }
  }, [fleetText]);

  const notifications = useMemo(
    () => (data?.notifications ?? []).filter((n) => !n.error),
    [data],
  );

  const totals = data?.totals;
  const council = unwrap(suite?.council_payload);
  const running = status === "running";

  const runningLabel =
    progress?.message ??
    (progress
      ? `${progress.step_label} (${progress.percent}%)`
      : "Running full fleet suite…");

  const statusLabel: Record<RunnerStatus, string> = {
    idle: "Ready — press Start full suite",
    running: runningLabel,
    done: "Last suite complete",
    error: "Run failed",
  };

  const statusColor: Record<RunnerStatus, string> = {
    idle: "bg-slate-700 text-slate-300",
    running: "bg-amber-500/20 text-amber-200 border-amber-500/40",
    done: "bg-emerald-500/20 text-emerald-200 border-emerald-500/40",
    error: "bg-red-500/20 text-red-200 border-red-500/40",
  };

  const tabs: { id: TabId; label: string; icon: typeof Bell; title: string }[] =
    [
      {
        id: "overview",
        label: "Overview",
        icon: Coffee,
        title: "Summary: pass/fail per step, suggested actions",
      },
      {
        id: "notifications",
        label: "Activity",
        icon: Bell,
        title: "New GitHub notifications since last run",
      },
      {
        id: "prs",
        label: "PRs",
        icon: GitPullRequest,
        title: "Open pull requests across fleet, stale markers",
      },
      {
        id: "issues",
        label: "Issues",
        icon: CircleDot,
        title: "Open issues across fleet, stale markers",
      },
      {
        id: "repos",
        label: "Repos",
        icon: ExternalLink,
        title: "Scanned repo links with PR/issue counts",
      },
      {
        id: "ci",
        label: "CI",
        icon: Workflow,
        title: "Failed or cancelled workflow runs (48h)",
      },
      {
        id: "security",
        label: "Security",
        icon: Shield,
        title: "Open Dependabot alerts by severity",
      },
      {
        id: "acks",
        label: "Ack drafts",
        icon: GitPullRequest,
        title: "Stale PRs needing a maintainer reply — drafts ready to send",
      },
      {
        id: "catalog",
        label: "Registry",
        icon: Database,
        title:
          "Registry metadata, port collisions, docs compliance, quarantined",
      },
      {
        id: "workspace",
        label: "Workspace",
        icon: CircleDot,
        title: "Local clone dirtiness and pyproject version drift",
      },
      {
        id: "links",
        label: "Links",
        icon: ExternalLink,
        title: "Scraper grade matrix and gitingest URLs",
      },
      {
        id: "retro",
        label: "Retro",
        icon: RefreshCw,
        title: "Merged PRs and new issues in the last 7 days",
      },
    ];

  return (
    <div className="space-y-5 max-w-5xl">
      <div className="flex items-start gap-3">
        <Coffee className="h-8 w-8 shrink-0 text-amber-400 mt-1" />
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            Breakfast runner
          </h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
            Full fleet maintainer suite — digest, CI, security, registry,
            workspace, grades. MCP:{" "}
            <code className="text-foreground/80">
              fleet_ops(operation=&quot;full_suite&quot;)
            </code>
          </p>
        </div>
      </div>

      <section className="rounded-xl border border-border bg-card/60 p-4 md:p-5 space-y-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span
              className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold border ${statusColor[status]}`}
            >
              {running && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              {statusLabel[status]}
            </span>
            {(suite?.generated_at ?? data?.generated_at) &&
              status !== "running" && (
                <span className="text-xs text-muted-foreground font-mono">
                  {new Date(
                    suite?.generated_at ?? data?.generated_at ?? "",
                  ).toLocaleString()}
                  {data?.maintainer ? ` · ${data.maintainer}` : ""}
                </span>
              )}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => run()}
              disabled={running}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold bg-amber-500 text-amber-950 hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed shadow-md transition-colors"
            >
              {running ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Play className="h-5 w-5 fill-current" />
              )}
              {running ? "Running…" : "Start full suite"}
            </button>
            {suite && !running && (
              <button
                type="button"
                onClick={() => run()}
                className="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium border border-border text-muted-foreground hover:text-foreground hover:bg-white/5"
              >
                <RefreshCw className="h-4 w-4" />
                Run again
              </button>
            )}
          </div>
        </div>

        {running && progress && (
          <div className="space-y-2" aria-live="polite">
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
              <span className="truncate max-w-[70%]">
                {progress.message ?? progress.step_label}
              </span>
              <span className="font-mono shrink-0">
                {progress.percent}% · step {progress.step_index}/
                {progress.step_total}
              </span>
            </div>
            <div
              className="h-2.5 rounded-full bg-slate-800/80 overflow-hidden border border-border/50"
              role="progressbar"
              aria-valuenow={progress.percent}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              <div
                className="h-full bg-gradient-to-r from-amber-600 to-amber-400 transition-[width] duration-300 ease-out"
                style={{
                  width: `${Math.min(100, Math.max(0, progress.percent))}%`,
                }}
              />
            </div>
            {progress.repo && (
              <p className="text-xs font-mono text-amber-200/90 truncate">
                {progress.repo}
                {typeof progress.repo_index === "number" &&
                typeof progress.repo_total === "number"
                  ? ` (${progress.repo_index}/${progress.repo_total})`
                  : ""}
              </p>
            )}
          </div>
        )}

        {lastMessage && status === "done" && (
          <p className="text-sm text-emerald-400/90">{lastMessage}</p>
        )}

        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs text-muted-foreground uppercase tracking-wide">
                Fleet repos
              </span>
              <button
                type="button"
                onClick={() => loadRegistry()}
                disabled={running || registryLoading}
                className="text-xs text-amber-400 hover:text-amber-300 disabled:opacity-50"
              >
                {registryLoading ? "Loading…" : "Load from fleet registry"}
              </button>
            </div>
            <textarea
              className="mt-1 w-full min-h-[88px] rounded-md border border-border bg-background/80 px-3 py-2 font-mono text-sm"
              value={fleetText}
              onChange={(e) => setFleetText(e.target.value)}
              placeholder="sandraschi/git-github-mcp"
              disabled={running}
            />
            <p className="text-[11px] text-muted-foreground mt-1">
              Shared with /inbox · one owner/repo per line
            </p>
          </div>
          <div className="space-y-3">
            <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer">
              <input
                type="checkbox"
                checked={useRegistry}
                onChange={(e) => setUseRegistry(e.target.checked)}
                disabled={running}
                className="rounded"
              />
              Use mcp-central-docs fleet registry (~140 repos) instead of
              textarea
            </label>
            <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer">
              <input
                type="checkbox"
                checked={sinceLastRun}
                onChange={(e) => setSinceLastRun(e.target.checked)}
                disabled={running}
                className="rounded"
              />
              Notifications only since last successful run
            </label>
            <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer">
              <input
                type="checkbox"
                checked={deliverFile}
                onChange={(e) => setDeliverFile(e.target.checked)}
                disabled={running}
                className="rounded"
              />
              Write markdown file (morning-digest.md)
            </label>
            <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer">
              <input
                type="checkbox"
                checked={deliverAiwatcher}
                onChange={(e) => setDeliverAiwatcher(e.target.checked)}
                disabled={running}
                className="rounded"
              />
              Push summary to aiwatcher fleet ingest
            </label>
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              Stale after
              <input
                type="number"
                min={1}
                max={90}
                value={staleDays}
                onChange={(e) => setStaleDays(Number(e.target.value) || 7)}
                disabled={running}
                className="w-14 px-2 py-1 rounded border border-border bg-background text-center"
              />
              days
            </label>
          </div>
        </div>
      </section>

      {error && (
        <div className="p-4 rounded-lg border border-red-900/50 bg-red-950/30 text-red-200 text-sm">
          {error}
          <p className="mt-2 text-xs opacity-80">
            Ensure <span className="font-mono text-white">gh auth login</span>{" "}
            and backend on port 10713.
          </p>
        </div>
      )}

      {!suite && status === "idle" && !error && (
        <div className="rounded-lg border border-dashed border-border p-12 text-center text-muted-foreground text-sm">
          No results yet. Click{" "}
          <strong className="text-foreground">Start full suite</strong> or load
          the fleet registry.
        </div>
      )}

      {council?.summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
          {Object.entries(council.summary).map(([k, v]) => (
            <div
              key={k}
              className="rounded-lg border border-border bg-card/40 px-3 py-2 text-center"
            >
              <div className="text-xl font-semibold text-amber-300">{v}</div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wide">
                {k.replace(/_/g, " ")}
              </div>
            </div>
          ))}
        </div>
      )}

      {totals && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {[
            {
              label: "Notifications",
              value: totals.notifications,
              accent: "text-rose-400",
            },
            {
              label: "Open PRs",
              value: totals.open_prs,
              accent: "text-emerald-400",
            },
            {
              label: "Open issues",
              value: totals.open_issues,
              accent: "text-sky-400",
            },
            {
              label: "Stale PRs",
              value: totals.stale_prs,
              accent: "text-amber-400",
            },
            {
              label: "Stale issues",
              value: totals.stale_issues,
              accent: "text-amber-400",
            },
          ].map((c) => (
            <div
              key={c.label}
              className="rounded-lg border border-border bg-card/40 px-3 py-2 text-center"
            >
              <div className={`text-xl font-semibold ${c.accent}`}>
                {c.value}
              </div>
              <div className="text-xs text-muted-foreground">{c.label}</div>
            </div>
          ))}
        </div>
      )}

      {suite && (
        <>
          <div className="flex flex-wrap items-center gap-2 overflow-x-auto pb-1">
            {tabs.map(({ id, label, icon: Icon, title }) => (
              <button
                key={id}
                type="button"
                title={title}
                onClick={() => setTab(id)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors border shrink-0 flex items-center gap-1.5 ${
                  tab === id
                    ? "bg-amber-500/15 text-amber-200 border-amber-500/35"
                    : "bg-card/60 text-muted-foreground border-border hover:text-foreground"
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </div>

          {running ? (
            <div className="flex justify-center py-16">
              <Loader2 className="animate-spin h-8 w-8 text-amber-500" />
            </div>
          ) : tab === "overview" ? (
            <OverviewPanel suite={suite} council={council} />
          ) : tab === "notifications" ? (
            <ItemList
              empty="No new notifications since last digest run."
              items={notifications.map((n, i) => ({
                key: `n-${i}`,
                repo: n.repository ?? "GitHub",
                repoUrl: n.repository
                  ? `https://github.com/${n.repository}`
                  : undefined,
                title: n.subject_title ?? n.title ?? "Notification",
                url: n.subject_url ?? "",
                meta: [
                  n.reason,
                  n.unread ? "unread" : "read",
                  relTime(n.updated_at),
                ]
                  .filter(Boolean)
                  .join(" · "),
                stale: Boolean(n.unread),
              }))}
            />
          ) : tab === "prs" ? (
            <ItemList
              empty="No open pull requests in fleet."
              items={(data?.open_prs ?? []).map((pr) => ({
                key: `${pr.repo_slug}-${pr.number}`,
                repo: pr.repo_slug,
                repoUrl: pr.repo_url,
                title: pr.title,
                url: pr.url,
                meta: [
                  `#${pr.number}`,
                  pr.author?.login,
                  pr.isDraft ? "draft" : null,
                  typeof pr.comments === "number"
                    ? `${pr.comments} comments`
                    : null,
                  relTime(pr.updatedAt ?? pr.createdAt),
                ]
                  .filter(Boolean)
                  .join(" · "),
                stale: pr.is_stale,
                staleReason: pr.stale_reason,
              }))}
            />
          ) : tab === "issues" ? (
            <ItemList
              empty="No open issues in fleet."
              items={(data?.open_issues ?? []).map((iss) => ({
                key: `${iss.repo_slug}-${iss.number}`,
                repo: iss.repo_slug,
                repoUrl: iss.repo_url,
                title: iss.title,
                url: iss.url,
                meta: [
                  `#${iss.number}`,
                  iss.author?.login,
                  relTime(iss.updatedAt ?? iss.createdAt),
                ]
                  .filter(Boolean)
                  .join(" · "),
                stale: iss.is_stale,
                staleReason: iss.stale_reason,
              }))}
            />
          ) : tab === "repos" ? (
            <RepoList links={data?.repo_links ?? []} />
          ) : tab === "ci" ? (
            <CiPanel ci={unwrap(suite.ci_pulse)} />
          ) : tab === "security" ? (
            <SecurityPanel sec={unwrap(suite.dependabot_digest)} />
          ) : tab === "acks" ? (
            <AckPanel acks={unwrap(suite.ack_drafts)} />
          ) : tab === "catalog" ? (
            <CatalogPanel
              registry={unwrap(suite.registry_load)}
              ports={unwrap(suite.port_audit)}
              docs={unwrap(suite.docs_gate)}
              quarantine={unwrap(suite.quarantine_report)}
            />
          ) : tab === "workspace" ? (
            <WorkspacePanel
              dirty={unwrap(suite.local_dirty)}
              drift={unwrap(suite.release_drift)}
            />
          ) : tab === "links" ? (
            <LinksPanel
              grades={unwrap(suite.grade_snapshot)}
              gitingest={unwrap(suite.gitingest_bundle)}
            />
          ) : (
            <RetroPanel
              runner={unwrap(suite.runner_status)}
              retro={unwrap(suite.weekly_retro)}
            />
          )}

          {(data?.repo_errors?.length ?? 0) > 0 && (
            <div className="text-xs text-amber-400/90 font-mono border border-amber-900/40 rounded p-3 bg-amber-950/20">
              {data?.repo_errors?.map((e) => (
                <div key={e}>{e}</div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function OverviewPanel({
  suite,
  council,
}: {
  suite: SuiteResult;
  council: { summary?: Record<string, number>; actions?: string[] } | null;
}) {
  const checks = [
    { label: "Morning digest", ok: suite.morning_digest?.success },
    { label: "Registry", ok: suite.registry_load?.success },
    { label: "CI pulse", ok: suite.ci_pulse?.success },
    { label: "Dependabot", ok: suite.dependabot_digest?.success },
    { label: "Port audit", ok: suite.port_audit?.success },
    { label: "Docs gate", ok: suite.docs_gate?.success },
    { label: "Local dirty", ok: suite.local_dirty?.success },
    { label: "Grade snapshot", ok: suite.grade_snapshot?.success },
  ];
  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-border p-4 grid sm:grid-cols-2 gap-2">
        {checks.map((c) => (
          <div
            key={c.label}
            className="flex items-center justify-between text-sm"
          >
            <span>{c.label}</span>
            <span className={c.ok ? "text-emerald-400" : "text-red-400"}>
              {c.ok ? "ok" : "failed"}
            </span>
          </div>
        ))}
      </div>
      {council?.actions && council.actions.length > 0 && (
        <div className="rounded-lg border border-border p-4">
          <h3 className="text-sm font-semibold mb-2">Suggested actions</h3>
          <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-1">
            {council.actions.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function RepoList({ links }: { links: RepoLink[] }) {
  if (links.length === 0) {
    return <EmptyPanel text="No repos scanned" />;
  }
  return (
    <div className="rounded-lg border border-border overflow-hidden">
      {links.map((r) => (
        <div
          key={r.slug}
          className="flex items-center justify-between gap-3 px-4 py-3 border-b border-border/80 last:border-0 hover:bg-white/[0.02]"
        >
          <a
            href={r.url}
            target="_blank"
            rel="noreferrer"
            className="text-sm font-medium hover:text-amber-300 flex items-center gap-2"
          >
            {r.slug}
            <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
          </a>
          <div className="text-xs text-muted-foreground font-mono">
            {r.open_prs} PRs · {r.open_issues} issues
          </div>
        </div>
      ))}
    </div>
  );
}

function CiPanel({
  ci,
}: {
  ci: { failure_count?: number; failures?: Record<string, unknown>[] } | null;
}) {
  const failures = ci?.failures ?? [];
  if (!ci) return <EmptyPanel text="CI pulse not run" />;
  if (failures.length === 0) {
    return (
      <EmptyPanel
        text={`No CI failures in last window (${ci.failure_count ?? 0})`}
      />
    );
  }
  return (
    <ItemList
      empty=""
      items={failures.map((f, i) => ({
        key: `ci-${i}`,
        repo: String(f.repo_slug ?? ""),
        repoUrl: String(f.repo_url ?? ""),
        title: String(f.name ?? "Workflow run"),
        url: String(f.url ?? ""),
        meta: [f.conclusion, f.branch, relTime(String(f.created_at ?? ""))]
          .filter(Boolean)
          .join(" · "),
        stale: true,
        staleReason: "CI failure",
      }))}
    />
  );
}

function SecurityPanel({
  sec,
}: {
  sec: { alert_count?: number; alerts?: Record<string, unknown>[] } | null;
}) {
  const alerts = sec?.alerts ?? [];
  if (!sec) return <EmptyPanel text="Security digest not run" />;
  if (alerts.length === 0)
    return <EmptyPanel text="No open Dependabot alerts" />;
  return (
    <ItemList
      empty=""
      items={alerts.map((a, i) => ({
        key: `sec-${i}`,
        repo: String(a.repo_slug ?? ""),
        repoUrl: String(a.repo_url ?? ""),
        title: String(a.package ?? "dependency alert"),
        url: String(a.url ?? ""),
        meta: [a.security_advisory ?? a.severity, a.state]
          .filter(Boolean)
          .join(" · "),
        stale: true,
        staleReason: "security",
      }))}
    />
  );
}

function AckPanel({
  acks,
}: {
  acks: { drafts?: Record<string, unknown>[] } | null;
}) {
  const drafts = acks?.drafts ?? [];
  if (!acks) return <EmptyPanel text="Ack drafts not run" />;
  if (drafts.length === 0)
    return <EmptyPanel text="No stale PRs need acknowledgment drafts" />;
  return (
    <div className="space-y-3">
      {drafts.map((d) => (
        <div
          key={`${d.repo_slug}-${d.pr_number}`}
          className="rounded-lg border border-border p-4 text-sm"
        >
          <a
            href={String(d.url ?? "")}
            target="_blank"
            rel="noreferrer"
            className="font-medium hover:text-amber-300"
          >
            {String(d.repo_slug)} #{String(d.pr_number)} — {String(d.title)}
          </a>
          <p className="text-xs text-muted-foreground mt-1">
            {String(d.stale_reason ?? "")}
          </p>
          <p className="text-xs mt-2 p-2 rounded bg-muted/50 text-muted-foreground whitespace-pre-wrap">
            {String(d.draft_body ?? "")}
          </p>
        </div>
      ))}
    </div>
  );
}

function CatalogPanel({
  registry,
  ports,
  docs,
  quarantine,
}: {
  registry: { entry_count?: number; github_repos?: string[] } | null;
  ports: {
    collision_count?: number;
    mismatch_count?: number;
    collisions?: Record<string, unknown>[];
    mismatches?: Record<string, unknown>[];
  } | null;
  docs: {
    non_compliant_count?: number;
    non_compliant?: Record<string, unknown>[];
  } | null;
  quarantine: { count?: number; repos?: Record<string, unknown>[] } | null;
}) {
  return (
    <div className="space-y-4 text-sm">
      <Section title="Registry">
        {registry ? (
          <p className="text-muted-foreground">
            {registry.entry_count ?? 0} entries ·{" "}
            {(registry.github_repos ?? []).length} GitHub slugs
          </p>
        ) : (
          <p className="text-muted-foreground">Not loaded</p>
        )}
      </Section>
      <Section
        title={`Port audit (${ports?.collision_count ?? 0} collisions, ${ports?.mismatch_count ?? 0} mismatches)`}
      >
        {(ports?.collisions ?? []).map((c) => (
          <div
            key={`port-${String(c.port)}`}
            className="text-amber-400 font-mono text-xs"
          >
            port {String(c.port)}: {JSON.stringify(c.repos)}
          </div>
        ))}
        {(ports?.mismatches ?? []).slice(0, 10).map((m) => (
          <div
            key={`mismatch-${String(m.id)}`}
            className="text-xs text-muted-foreground"
          >
            {String(m.id)} {String(m.kind)} registry={String(m.registry_port)}{" "}
            doc={JSON.stringify(m.webapp_ports_doc)}
          </div>
        ))}
      </Section>
      <Section
        title={`Docs gate (${docs?.non_compliant_count ?? 0} non-compliant)`}
      >
        {(docs?.non_compliant ?? []).slice(0, 15).map((r) => (
          <div key={String(r.id)} className="text-xs text-muted-foreground">
            {String(r.id)}: missing {JSON.stringify(r.missing)}
          </div>
        ))}
      </Section>
      <Section title={`Quarantine (${quarantine?.count ?? 0})`}>
        {(quarantine?.repos ?? []).map((r) => (
          <div key={String(r.id)} className="text-xs">
            <span className="font-mono">{String(r.slug)}</span>
            <span className="text-muted-foreground">
              {" "}
              — {String(r.open_prs)} PRs, {String(r.open_issues)} issues
              {r.superseded_by
                ? ` · superseded by ${String(r.superseded_by)}`
                : ""}
            </span>
          </div>
        ))}
      </Section>
    </div>
  );
}

function WorkspacePanel({
  dirty,
  drift,
}: {
  dirty: {
    dirty_count?: number;
    dirty?: Record<string, unknown>[];
    sync_drift?: Record<string, unknown>[];
  } | null;
  drift: { drift_count?: number; drifts?: Record<string, unknown>[] } | null;
}) {
  return (
    <div className="space-y-4 text-sm">
      <Section title={`Dirty worktrees (${dirty?.dirty_count ?? 0})`}>
        {(dirty?.dirty ?? []).map((d) => (
          <div key={String(d.id)} className="text-xs font-mono text-amber-300">
            {String(d.id)} — {String(d.changed_files)} files
          </div>
        ))}
      </Section>
      <Section title="Sync drift">
        {(dirty?.sync_drift ?? []).map((d) => (
          <div key={String(d.id)} className="text-xs text-muted-foreground">
            {String(d.id)}: ahead {String(d.ahead)} / behind {String(d.behind)}
          </div>
        ))}
      </Section>
      <Section title={`Release drift (${drift?.drift_count ?? 0})`}>
        {(drift?.drifts ?? []).map((d) => (
          <div key={String(d.repo_slug)} className="text-xs">
            {String(d.repo_slug)}: local {String(d.local_version)} vs tag{" "}
            {String(d.latest_release_tag ?? "none")}
          </div>
        ))}
      </Section>
    </div>
  );
}

function LinksPanel({
  grades,
  gitingest,
}: {
  grades: {
    ok?: boolean;
    error?: string;
    repo_count?: number;
    recovery_options?: string[];
  } | null;
  gitingest: { links?: { repo_slug: string; gitingest_url: string }[] } | null;
}) {
  return (
    <div className="space-y-4 text-sm">
      <Section title="Grade snapshot (scraper-mcp)">
        {grades?.ok ? (
          <p className="text-muted-foreground">
            {grades.repo_count ?? "?"} repos in matrix
          </p>
        ) : (
          <div className="space-y-2">
            <p className="text-amber-400">
              {grades?.error ?? "scraper-mcp not running"}
            </p>
            {grades?.recovery_options && grades.recovery_options.length > 0 && (
              <div className="mono text-[11px] space-y-1">
                {grades.recovery_options.map((cmd: string) => (
                  <code
                    key={cmd}
                    className="block px-2 py-1 rounded bg-black/30 text-amber-300"
                  >
                    {cmd}
                  </code>
                ))}
              </div>
            )}
          </div>
        )}
      </Section>
      <Section title={`Gitingest (${gitingest?.links?.length ?? 0})`}>
        <div className="rounded-lg border border-border overflow-hidden max-h-64 overflow-y-auto">
          {(gitingest?.links ?? []).map((l) => (
            <a
              key={l.repo_slug}
              href={l.gitingest_url}
              target="_blank"
              rel="noreferrer"
              className="block px-4 py-2 text-xs font-mono border-b border-border/80 hover:bg-white/[0.02]"
            >
              {l.repo_slug}
            </a>
          ))}
        </div>
      </Section>
    </div>
  );
}

function RetroPanel({
  runner,
  retro,
}: {
  runner: {
    last_run_at?: string;
    scheduled_task?: { installed?: boolean };
  } | null;
  retro: {
    merged_pr_count?: number;
    new_issue_count?: number;
    merged_prs?: Record<string, unknown>[];
  } | null;
}) {
  return (
    <div className="space-y-4 text-sm">
      <Section title="Scheduled runner">
        <p className="text-muted-foreground">
          Task installed: {runner?.scheduled_task?.installed ? "yes" : "no"}
          {runner?.last_run_at
            ? ` · last run ${new Date(runner.last_run_at).toLocaleString()}`
            : ""}
        </p>
      </Section>
      <Section
        title={`Weekly retro (${retro?.merged_pr_count ?? 0} merged PRs, ${retro?.new_issue_count ?? 0} new issues)`}
      >
        <ItemList
          empty="No merged PRs this week"
          items={(retro?.merged_prs ?? []).map((pr, i) => ({
            key: `m-${i}`,
            repo: String(pr.repo_slug ?? ""),
            repoUrl: "",
            title: String(pr.title ?? ""),
            url: String(pr.url ?? ""),
            meta: [
              pr.author && typeof pr.author === "object"
                ? (pr.author as Author).login
                : null,
              relTime(String(pr.mergedAt ?? "")),
            ]
              .filter(Boolean)
              .join(" · "),
          }))}
        />
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <h3 className="text-sm font-semibold mb-2">{title}</h3>
      {children}
    </div>
  );
}

function EmptyPanel({ text }: { text: string }) {
  return (
    <div className="p-10 text-center text-muted-foreground text-sm rounded-lg border border-border">
      {text}
    </div>
  );
}

type RowItem = {
  key: string;
  repo: string;
  repoUrl?: string;
  title: string;
  url: string;
  meta: string;
  stale?: boolean;
  staleReason?: string;
};

function ItemList({ empty, items }: { empty: string; items: RowItem[] }) {
  if (items.length === 0) {
    return <EmptyPanel text={empty} />;
  }
  return (
    <div className="rounded-lg border border-border overflow-hidden">
      {items.map((row) => (
        <div
          key={row.key}
          className="flex items-start gap-3 px-4 py-3 border-b border-border/80 last:border-0 hover:bg-white/[0.02]"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              {row.repoUrl ? (
                <a
                  href={row.repoUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs font-mono px-1.5 py-0.5 rounded bg-muted text-foreground hover:text-amber-300"
                >
                  {row.repo}
                </a>
              ) : (
                <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-muted">
                  {row.repo}
                </span>
              )}
              {row.stale && (
                <span className="text-xs text-amber-400 border border-amber-700/50 rounded px-1.5 py-0">
                  {row.staleReason ?? "needs attention"}
                </span>
              )}
            </div>
            {row.url ? (
              <a
                href={row.url}
                target="_blank"
                rel="noreferrer"
                className="text-sm font-medium hover:underline block truncate mt-1"
              >
                {row.title}
              </a>
            ) : (
              <span className="text-sm font-medium block truncate mt-1">
                {row.title}
              </span>
            )}
            <div className="text-xs text-muted-foreground mt-1">{row.meta}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
