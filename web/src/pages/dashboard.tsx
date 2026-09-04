import {
  AlertCircle,
  BarChart3,
  CircleDot,
  ExternalLink,
  GitBranch,
  GitCommit,
  GitPullRequest,
  Search,
  Star,
  Terminal,
  TrendingUp,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useEffect, useState } from "react";
import { getStatus, githubOps, gitOps } from "@/lib/api";

interface StatusData {
  git_available?: boolean;
  gh_available?: boolean;
  gh_authenticated?: boolean;
}
interface RepoStatus {
  success: boolean;
  data?: { branch: string; remote_url: string; total_changes: number };
}
interface LogData {
  success: boolean;
  data?: {
    count: number;
    entries: Array<{
      hash: string;
      author: string;
      date: string;
      subject: string;
    }>;
  };
}

export function Dashboard() {
  const [sysStatus, setSysStatus] = useState<StatusData | null>(null);
  const [repoStatus, setRepoStatus] = useState<RepoStatus | null>(null);
  const [recentLog, setRecentLog] = useState<LogData | null>(null);
  const [myRepos, setMyRepos] = useState<
    { name: string; url: string; stargazerCount: number }[]
  >([]);
  const [starsSummary, setStarsSummary] = useState<{
    total_stars: number;
    total_repos: number;
    avg_stars: number;
    zero_star_repos: number;
    distribution: Record<string, number>;
    top_repos: { name: string; stargazerCount: number }[];
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [repoPath, setRepoPath] = useState("D:/Dev/repos/git-github-mcp");

  useEffect(() => {
    Promise.allSettled([
      getStatus().then((d) => setSysStatus(d as StatusData)),
      (
        gitOps("status", { repo_path: repoPath }) as Promise<{
          result?: RepoStatus["data"];
        }>
      )
        .then((d) => {
          if (d?.result) setRepoStatus({ success: true, data: d.result });
        })
        .catch(() => {}),
      (
        gitOps("log", { repo_path: repoPath, max_count: 8 }) as Promise<{
          result?: LogData["data"];
        }>
      )
        .then((d) => {
          if (d?.result) setRecentLog({ success: true, data: d.result });
        })
        .catch(() => {}),
      (
        githubOps("repo_list", { limit: 8 }) as Promise<{
          result: { repos: typeof myRepos };
        }>
      )
        .then((d) => setMyRepos(d?.result?.repos ?? []))
        .catch(() => {}),
      (
        githubOps("stars_summary", { owner: "sandraschi", limit: 5 }) as Promise<{
          result?: typeof starsSummary;
        }>
      )
        .then((d) => {
          if (d?.result) setStarsSummary(d.result);
        })
        .catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [repoPath]);

  const online = sysStatus?.git_available;
  const ghAuth = sysStatus?.gh_authenticated;

  return (
    <div
      className="space-y-8 animate-in fade-in duration-700"
      data-testid="dashboard"
    >
      {/* Hero - compact professional */}
      <div className="rounded-2xl border border-border bg-gradient-to-br from-card via-card to-black/20 p-5 md:p-6" data-testid="dashboard-hero">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/10 text-xs font-mono">
              <span className="w-2 h-2 rounded-full bg-gh-green shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
              git-github-mcp <span className="text-muted-foreground">· local & remote Git</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
              Repos, branches & PRs — one place
            </h1>
            <p className="text-sm text-muted-foreground max-w-[50ch] leading-relaxed">
              Local git and GitHub together. Set a repo path, check branches and changes, read commits and jump to cloud repos and stars.
            </p>
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <a
                href="/repos"
                data-testid="hero-cta-repos"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white text-black text-sm font-semibold hover:bg-zinc-200 transition-colors"
              >
                <GitBranch className="w-4 h-4" /> Browse repos
              </a>
              <a
                href="/stars"
                data-testid="hero-cta-stars"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gh-green/10 border border-gh-green/20 text-gh-green text-sm font-semibold hover:bg-gh-green/15 transition-colors"
              >
                View stars
              </a>
              <span className="text-xs text-muted-foreground font-mono ml-1">Active context below</span>
            </div>
          </div>

          <div className="flex flex-col gap-3 shrink-0">
            <div className="flex items-center gap-2 p-1 rounded-lg bg-black/30 border border-white/10 backdrop-blur-sm self-start">
              <StatusBadge
                label="GIT"
                online={online}
                icon={Wifi}
                offIcon={WifiOff}
                colorClass={online ? "text-gh-green" : "text-destructive"}
              />
              <div className="w-px h-4 bg-white/10" />
              <StatusBadge
                label="GH"
                online={ghAuth}
                icon={CircleDot}
                offIcon={AlertCircle}
                colorClass={ghAuth ? "text-gh-blue" : "text-amber-500"}
              />
            </div>
            <div className="text-xs font-mono text-muted-foreground">
              {online ? "git ready" : "git not found"} · {ghAuth ? "GitHub authenticated" : "run gh auth login"}
            </div>
          </div>
        </div>
      </div>

      {/* Repo Configuration */}
      <div className="group relative">
        <div className="absolute -inset-1 bg-gradient-to-r from-gh-green/20 to-gh-blue/20 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200" />
        <div className="relative flex items-center gap-4 p-4 rounded-xl glass-dark border-border/50">
          <Terminal className="w-4 h-4 text-gh-green" />
          <div className="flex-1 space-y-1">
            <label
              htmlFor="active-context-path"
              className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 px-1"
            >
              Active Context
            </label>
            <input
              id="active-context-path"
              className="w-full bg-transparent text-sm font-mono text-gh-green outline-none selection:bg-gh-green/20"
              value={repoPath}
              onChange={(e) => setRepoPath(e.target.value)}
              onBlur={() => {
                setLoading(true);
              }}
              placeholder="System path to local git repository..."
            />
          </div>
        </div>
      </div>

      {/* Analytics Grid - denser 6 */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
        <MetricCard
          label="Active Branch"
          value={repoStatus?.data?.branch}
          icon={GitBranch}
          loading={loading}
          color="text-gh-green"
          testid="kpi-branch"
        />
        <MetricCard
          label="Pending Sync"
          value={repoStatus?.data?.total_changes}
          icon={AlertCircle}
          loading={loading}
          color="text-amber-500"
          testid="kpi-pending"
        />
        <MetricCard
          label="Commit History"
          value={recentLog?.data?.count}
          icon={GitCommit}
          loading={loading}
          color="text-gh-blue"
          testid="kpi-commits"
        />
        <MetricCard
          label="Cloud Repos"
          value={starsSummary?.total_repos ?? myRepos.length}
          icon={GitPullRequest}
          loading={loading}
          color="text-purple-400"
          testid="kpi-cloud"
        />
        <MetricCard
          label="Total Stars"
          value={starsSummary?.total_stars}
          icon={Star}
          loading={loading}
          color="text-amber-400"
          testid="kpi-stars"
        />
        <MetricCard
          label="Avg Stars"
          value={starsSummary?.avg_stars}
          icon={TrendingUp}
          loading={loading}
          color="text-sky-400"
          testid="kpi-avg"
        />
      </div>

      {/* Dense second row: Stars + Quick actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass rounded-2xl border-border/50 p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold tracking-tight uppercase flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-amber-400" /> Stars at a glance
            </h2>
            <a href="/stars" className="text-xs font-mono text-gh-blue hover:underline flex items-center gap-1">
              details <ExternalLink className="w-3 h-3" />
            </a>
          </div>
          {starsSummary ? (
            <div className="mt-4 space-y-3">
              <div className="flex flex-wrap gap-2 text-xs font-mono">
                <span className="px-2 py-1 rounded bg-amber-500/10 border border-amber-500/20 text-amber-400">total {starsSummary.total_stars}</span>
                <span className="px-2 py-1 rounded bg-white/5 border border-white/10">repos {starsSummary.total_repos}</span>
                <span className="px-2 py-1 rounded bg-white/5 border border-white/10">avg {starsSummary.avg_stars}</span>
                <span className="px-2 py-1 rounded bg-red-500/10 border border-red-500/20 text-red-300">zero {starsSummary.zero_star_repos}</span>
              </div>
              <div className="grid gap-1.5">
                {Object.entries(starsSummary.distribution).map(([bucket, count]) => {
                  const pct = (count / Math.max(1, starsSummary.total_repos)) * 100;
                  return (
                    <div key={bucket} className="flex items-center gap-2">
                      <span className="w-12 text-xs font-mono text-muted-foreground text-right">{bucket}</span>
                      <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
                        <div className="h-full bg-amber-400 rounded-full" style={{ width: `${pct}%` }} />
                      </div>
                      <span className="w-12 text-xs font-mono text-right">{count}</span>
                    </div>
                  );
                })}
              </div>
              {starsSummary.top_repos?.length ? (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {starsSummary.top_repos.slice(0, 5).map((r) => (
                    <span key={r.name} className="inline-flex items-center gap-1 px-2 py-1 rounded bg-white/5 border border-white/10 text-xs font-mono">
                      <Star className="w-3 h-3 text-amber-400" /> {r.name} {r.stargazerCount}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
          ) : (
            <div className="mt-4 text-sm text-muted-foreground">{loading ? "Loading stars…" : "No stars data"}</div>
          )}
        </div>

        <div className="glass rounded-2xl border-border/50 p-5">
          <h2 className="text-sm font-bold tracking-tight uppercase flex items-center gap-2">
            <Search className="w-4 h-4 text-gh-blue" /> Quick actions
          </h2>
          <div className="mt-4 grid grid-cols-2 gap-2">
            <a href="/repos" className="p-3 rounded-xl bg-white text-black text-sm font-semibold hover:bg-zinc-200 transition-colors flex items-center gap-2">
              <GitBranch className="w-4 h-4" /> Repos
            </a>
            <a href="/stars" className="p-3 rounded-xl bg-amber-500 text-black text-sm font-semibold hover:bg-amber-400 transition-colors flex items-center gap-2">
              <Star className="w-4 h-4" /> Stars
            </a>
            <a href="/commits" className="p-3 rounded-xl bg-white/5 border border-white/10 text-sm hover:bg-white/10 transition-colors flex items-center gap-2">
              <GitCommit className="w-4 h-4" /> Commits
            </a>
            <a href="/pull-requests" className="p-3 rounded-xl bg-white/5 border border-white/10 text-sm hover:bg-white/10 transition-colors flex items-center gap-2">
              <GitPullRequest className="w-4 h-4" /> PRs
            </a>
            <a href="/issues" className="p-3 rounded-xl bg-white/5 border border-white/10 text-sm hover:bg-white/10 transition-colors flex items-center gap-2">
              <CircleDot className="w-4 h-4" /> Issues
            </a>
            <a href="/tools" className="p-3 rounded-xl bg-white/5 border border-white/10 text-sm hover:bg-white/10 transition-colors flex items-center gap-2">
              <Terminal className="w-4 h-4" /> Tools
            </a>
          </div>
          <div className="mt-3 text-xs text-muted-foreground font-mono">
            Ports :{typeof window !== "undefined" ? `${Number(window.location.port) - 1} / :${window.location.port}` : "backend / :frontend"} · {online ? "git ok" : "git missing"} · {ghAuth ? "gh auth ok" : "gh auth needed"}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Commit Log */}
        <div className="lg:col-span-2 glass rounded-2xl overflow-hidden border-border/50">
          <div className="px-6 py-4 border-b border-white/5 bg-white/5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <GitCommit className="w-4 h-4 text-gh-green" />
              <h2 className="text-sm font-bold tracking-tight uppercase">
                Recent Changes
              </h2>
            </div>
            <span className="text-[10px] font-mono text-muted-foreground bg-black/40 px-2 py-0.5 rounded border border-white/5 uppercase">
              {repoPath.split("/").pop() || "fs"}
            </span>
          </div>

          <div className="divide-y divide-white/5">
            {loading ? (
              <LoadingState />
            ) : recentLog?.data?.entries?.length ? (
              recentLog.data.entries.map((e) => (
                <div
                  key={e.hash}
                  className="group flex items-center gap-4 px-6 py-3.5 hover:bg-gh-green/[0.03] transition-all"
                >
                  <span className="font-mono text-[10px] font-bold text-gh-green bg-gh-green/10 px-2 py-1 rounded border border-gh-green/20 group-hover:border-gh-green/40 transition-all">
                    {e.hash.slice(0, 7)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-foreground/90 truncate group-hover:text-foreground transition-colors leading-tight">
                      {e.subject}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] text-muted-foreground capitalize">
                        {e.author.split(" ")[0]}
                      </span>
                      <div className="w-0.5 h-0.5 rounded-full bg-white/20" />
                      <span className="text-[10px] text-muted-foreground font-mono">
                        {e.date}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <EmptyState
                message={
                  recentLog?.success === false
                    ? "No Git repository detected"
                    : "Commit history is empty"
                }
              />
            )}
          </div>
        </div>

        {/* GitHub Fleet */}
        <div className="glass rounded-2xl overflow-hidden border-border/50">
          <div className="px-6 py-4 border-b border-white/5 bg-white/5 flex items-center gap-2">
            <CircleDot className="w-4 h-4 text-gh-blue" />
            <h2 className="text-sm font-bold tracking-tight uppercase">
              Cloud Fleet
            </h2>
          </div>

          <div className="divide-y divide-white/5 flex flex-col h-full">
            {myRepos.length > 0 ? (
              myRepos.map((r) => (
                <div
                  key={r.name}
                  className="flex items-center gap-3 px-6 py-4 hover:bg-gh-blue/[0.03] transition-all group"
                >
                  <div className="h-2 w-2 rounded-full bg-gh-green shadow-[0_0_8px_rgba(34,197,94,0.4)] group-hover:scale-125 transition-transform" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-mono text-foreground truncate">
                      {r.name}
                    </p>
                    <div className="flex items-center gap-1.5 mt-0.5 text-[10px] text-muted-foreground">
                      <Wifi className="w-2.5 h-2.5" />
                      <span>Authenticated</span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="text-[10px] font-mono text-muted-foreground">
                      ★ {r.stargazerCount}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <EmptyState message="No cloud repositories found" />
            )}
            <div className="flex-1 bg-black/20" />
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({
  label,
  online,
  icon: Icon,
  offIcon: OffIcon,
  colorClass,
}: {
  label: string;
  online?: boolean;
  icon: React.ElementType;
  offIcon: React.ElementType;
  colorClass: string;
}) {
  return (
    <div
      className={`flex items-center gap-1.5 px-2 py-1 rounded-md transition-all ${online ? "bg-white/5" : "bg-destructive/10"}`}
    >
      {online ? (
        <Icon className={`w-3 h-3 ${colorClass}`} />
      ) : (
        <OffIcon className="w-3 h-3 text-destructive" />
      )}
      <span
        className={`text-[10px] font-bold uppercase tracking-tight ${online ? "text-foreground/80" : "text-destructive/80"}`}
      >
        {label}: {online ? "OK" : "FAIL"}
      </span>
    </div>
  );
}

function MetricCard({
  label,
  value,
  icon: Icon,
  loading,
  color,
  testid,
}: {
  label: string;
  value?: string | number;
  icon: React.ElementType;
  loading: boolean;
  color: string;
  testid?: string;
}) {
  return (
    <div
      className="glass p-5 rounded-2xl relative overflow-hidden group hover:border-gh-green/30 transition-all"
      data-testid={testid}
    >
      <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
        <Icon className="w-12 h-12" />
      </div>
      <div className="flex flex-col gap-2">
        <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground/60">
          {label}
        </span>
        <div
          className={`text-2xl font-black font-mono tracking-tight flex items-center gap-2 ${color}`}
        >
          {loading ? (
            <div className="h-8 w-16 bg-white/5 animate-pulse rounded" />
          ) : (
            <span className="truncate">{String(value ?? "--")}</span>
          )}
          {!loading && value === "main" && (
            <div className="h-1.5 w-1.5 rounded-full bg-gh-green shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
          )}
        </div>
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="p-12 flex flex-col items-center justify-center gap-3">
      <div className="w-8 h-8 border-2 border-gh-green/20 border-t-gh-green rounded-full animate-spin" />
      <span className="text-xs font-mono text-muted-foreground uppercase tracking-widest">
        Aggregating...
      </span>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="p-12 flex flex-col items-center justify-center text-center">
      <AlertCircle className="w-8 h-8 text-muted-foreground/20 mb-3" />
      <p className="text-sm text-muted-foreground font-mono">{message}</p>
    </div>
  );
}
