import {
  AlertCircle,
  AreaChart,
  Calendar,
  Crown,
  ExternalLink,
  Github,
  Loader2,
  RefreshCw,
  Search,
  Star,
  TrendingUp,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { githubOps } from "@/lib/api";

interface TopRepo {
  name: string;
  description: string;
  isPrivate: boolean;
  stargazerCount: number;
  forkCount: number;
  updatedAt: string;
  pushedAt?: string;
  url: string;
  language?: string;
}

interface StarsSummary {
  owner: string;
  total_repos: number;
  total_stars: number;
  total_forks: number;
  avg_stars: number;
  median_stars: number;
  zero_star_repos: number;
  distribution: Record<string, number>;
  top_repos: TopRepo[];
  visibility: string;
  fetched_at: string;
}

interface HistoryPoint {
  bucket: string;
  new: number;
  cumulative: number;
}

interface StarsHistory {
  owner: string;
  repo: string | null;
  bucket: string;
  points: HistoryPoint[];
  per_repo: Record<string, number>;
  total_events: number;
  repos_scanned: number;
  failed_repos?: string[];
  note?: string;
}

export function StarsPage() {
  const [owner, setOwner] = useState("sandraschi");
  const [data, setData] = useState<StarsSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [perRepoQuery, setPerRepoQuery] = useState("");
  const [perRepoResult, setPerRepoResult] = useState<TopRepo | null>(null);
  const [perRepoLoading, setPerRepoLoading] = useState(false);
  const [history, setHistory] = useState<StarsHistory | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyBucket, setHistoryBucket] = useState<"month" | "week" | "day">("month");
  const [historyRepo, setHistoryRepo] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = (await githubOps("stars_summary", {
        owner: owner.trim() || undefined,
        limit: 50,
      })) as { success: boolean; result?: StarsSummary; error?: string };
      if (!res.success) throw new Error(res.error || "failed");
      if (res.result) setData(res.result);
      else throw new Error("no result");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [owner]);

  useEffect(() => {
    load();
  }, [load]);

  const fetchPerRepo = async () => {
    if (!perRepoQuery.trim()) return;
    setPerRepoLoading(true);
    setPerRepoResult(null);
    try {
      // perRepoQuery can be "repo" or "owner/repo"
      let qOwner = owner.trim();
      let qRepo = perRepoQuery.trim();
      if (qRepo.includes("/")) {
        const parts = qRepo.split("/");
        qOwner = parts[0];
        qRepo = parts[1];
      }
      const res = (await githubOps("stars_per_repo", {
        owner: qOwner,
        repo: qRepo,
      })) as {
        success: boolean;
        result?: Record<string, unknown>;
        error?: string;
      };
      if (!res.success) throw new Error(res.error || "failed");
      const r = res.result as unknown as Record<string, unknown>;
      // normalize
      setPerRepoResult({
        name: (r["name"] as string) || qRepo,
        description: (r["description"] as string) || "",
        isPrivate: (r["isPrivate"] as boolean) ?? (r["private"] as boolean) ?? false,
        stargazerCount: (r["stargazerCount"] as number) ?? (r["stargazers_count"] as number) ?? 0,
        forkCount: (r["forkCount"] as number) ?? (r["forks_count"] as number) ?? 0,
        updatedAt: (r["updatedAt"] as string) || (r["updated_at"] as string) || "",
        url: (r["url"] as string) || `https://github.com/${qOwner}/${qRepo}`,
        language: r["language"] as string,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setPerRepoLoading(false);
    }
  };

  const fetchHistory = async () => {
    setHistoryLoading(true);
    setError(null);
    try {
      const res = (await githubOps("stars_history", {
        owner: owner.trim() || undefined,
        repo: historyRepo.trim() || undefined,
        query: historyBucket,
        limit: 30,
      })) as { success: boolean; result?: StarsHistory; error?: string };
      if (!res.success) throw new Error(res.error || "failed");
      if (res.result) setHistory(res.result);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setHistoryLoading(false);
    }
  };

  const filtered =
    data?.top_repos.filter(
      (r) =>
        !filter ||
        r.name.toLowerCase().includes(filter.toLowerCase()) ||
        (r.description ?? "").toLowerCase().includes(filter.toLowerCase()),
    ) ?? [];

  const maxStars = Math.max(
    1,
    ...(data?.top_repos.map((r) => r.stargazerCount) ?? [1]),
  );

  return (
    <div className="space-y-6 max-w-6xl" data-testid="stars-page">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight flex items-center gap-3">
            <span className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
              <Star size={18} className="text-amber-400" />
            </span>
            Stars — Received
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Total stars your repos earned (via{" "}
            <span className="font-mono text-xs">stargazerCount</span>) +
            per-repo leaderboard. Not the “Stars tab” you give.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            <Github size={14} className="text-muted-foreground" />
            <input
              data-testid="stars-owner-input"
              className="bg-card border border-border rounded-md px-3 py-1.5 text-sm font-mono w-40 focus:outline-none focus:ring-1 focus:ring-amber-500/50"
              value={owner}
              onChange={(e) => setOwner(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && load()}
              placeholder="owner"
            />
          </div>
          <button
            type="button"
            data-testid="stars-refresh"
            onClick={load}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-400 hover:bg-amber-500/20 text-sm font-medium disabled:opacity-50 transition-colors"
          >
            {loading ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <RefreshCw size={14} />
            )}
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-sm text-red-300">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          <div>
            <div className="font-semibold">Failed to load stars</div>
            <div className="font-mono text-xs mt-1 break-all">{error}</div>
            <div className="text-xs mt-2 text-red-300/70">
              Tip: run <span className="font-mono">gh auth login</span> then
              restart backend.
            </div>
          </div>
        </div>
      )}

      {/* KPIs */}
      {data ? (
        <>
          <div className="grid gap-3 grid-cols-2 lg:grid-cols-5">
            <div
              className="rounded-xl border border-border bg-card/50 p-4"
              data-testid="kpi-total-stars"
            >
              <div className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
                Total stars
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-3xl font-black text-amber-400">
                  {data.total_stars}
                </span>
                <Star size={16} className="text-amber-400/60" />
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {data.total_repos} repos
              </div>
            </div>
            <div
              className="rounded-xl border border-border bg-card/50 p-4"
              data-testid="kpi-avg"
            >
              <div className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
                Avg / median
              </div>
              <div className="mt-2 text-xl font-bold">
                {data.avg_stars}{" "}
                <span className="text-sm font-normal text-muted-foreground">
                  / {data.median_stars}
                </span>
              </div>
              <div className="text-xs text-muted-foreground mt-1">per repo</div>
            </div>
            <div
              className="rounded-xl border border-border bg-card/50 p-4"
              data-testid="kpi-forks"
            >
              <div className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
                Forks
              </div>
              <div className="mt-2 text-2xl font-black">{data.total_forks}</div>
              <div className="text-xs text-muted-foreground mt-1">
                total forks
              </div>
            </div>
            <div
              className="rounded-xl border border-border bg-card/50 p-4"
              data-testid="kpi-zero"
            >
              <div className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
                Zero-star
              </div>
              <div className="mt-2 text-2xl font-black">
                {data.zero_star_repos}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                need love
              </div>
            </div>
            <div
              className="rounded-xl border border-border bg-card/50 p-4"
              data-testid="kpi-updated"
            >
              <div className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
                Fetched
              </div>
              <div className="mt-2 text-xs font-mono">
                {new Date(data.fetched_at).toLocaleString()}
              </div>
              <div className="text-xs text-muted-foreground mt-1 capitalize">
                {data.visibility}
              </div>
            </div>
          </div>

          {/* Distribution */}
          <div className="rounded-xl border border-border bg-card/50 p-5">
            <h2 className="text-sm font-bold flex items-center gap-2">
              <TrendingUp size={14} className="text-amber-400" /> Distribution
            </h2>
            <div className="mt-4 grid gap-2">
              {Object.entries(data.distribution).map(([bucket, count]) => {
                const pct = data.total_repos
                  ? (count / data.total_repos) * 100
                  : 0;
                return (
                  <div key={bucket} className="flex items-center gap-3">
                    <span className="w-14 text-xs font-mono text-muted-foreground text-right">
                      {bucket}
                    </span>
                    <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                      <div
                        className="h-full bg-amber-500/70 rounded-full transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="w-16 text-xs font-mono text-right">
                      {count}{" "}
                      <span className="text-muted-foreground">
                        ({pct.toFixed(0)}%)
                      </span>
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Trajectory */}
          <div className="rounded-xl border border-border bg-card/50 p-5" data-testid="stars-trajectory">
            <h2 className="text-sm font-bold flex items-center gap-2">
              <AreaChart size={14} className="text-amber-400" /> Trajectory — stars over time
            </h2>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-1.5">
                <Calendar size={12} className="text-muted-foreground" />
                <select
                  data-testid="trajectory-bucket"
                  value={historyBucket}
                  onChange={(e) => setHistoryBucket(e.target.value as never)}
                  className="bg-background border border-border rounded-md px-2 py-1 text-xs font-mono"
                >
                  <option value="month">per month</option>
                  <option value="week">per week</option>
                  <option value="day">per day</option>
                </select>
              </div>
              <input
                data-testid="trajectory-repo"
                className="bg-background border border-border rounded-md px-2 py-1 text-xs font-mono w-44 focus:outline-none focus:ring-1 focus:ring-amber-500/20"
                placeholder="repo (blank = all top 30)"
                value={historyRepo}
                onChange={(e) => setHistoryRepo(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && fetchHistory()}
              />
              <button
                type="button"
                data-testid="trajectory-load"
                onClick={fetchHistory}
                disabled={historyLoading}
                className="px-3 py-1 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-semibold hover:bg-amber-500/20 disabled:opacity-50"
              >
                {historyLoading ? <Loader2 size={12} className="animate-spin" /> : "Load trajectory"}
              </button>
              {history && <span className="text-xs text-muted-foreground font-mono">{history.total_events} events · {history.repos_scanned} repos</span>}
            </div>
            {history?.note && (
              <div className="mt-3 p-3 rounded-lg bg-amber-500/5 border border-amber-500/20 text-xs text-amber-200">{history.note}</div>
            )}
            {history && history.points.length > 0 ? (
              <div className="mt-4">
                {/* Pure SVG area - no extra deps */}
                {(() => {
                  const pts = history.points;
                  const w = 800;
                  const h = 160;
                  const padL = 40;
                  const padR = 12;
                  const padT = 12;
                  const padB = 24;
                  const maxC = Math.max(1, ...pts.map((p) => p.cumulative));
                  const maxN = Math.max(1, ...pts.map((p) => p.new));
                  const xStep = (w - padL - padR) / Math.max(1, pts.length - 1);
                  const yC = (v: number) => h - padB - (v / maxC) * (h - padT - padB);
                  const yN = (v: number) => h - padB - (v / maxN) * (h - padT - padB) * 0.35;
                  const pathC = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${padL + i * xStep} ${yC(p.cumulative)}`).join(" ");
                  const areaC = `${pathC} L ${padL + (pts.length - 1) * xStep} ${h - padB} L ${padL} ${h - padB} Z`;
                  const pathN = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${padL + i * xStep} ${yN(p.new)}`).join(" ");
                  return (
                    <div className="overflow-x-auto">
                      <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-[180px] border border-border/30 rounded-lg bg-black/20">
                        <defs>
                          <linearGradient id="gradC" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.35} />
                            <stop offset="100%" stopColor="#f59e0b" stopOpacity={0.02} />
                          </linearGradient>
                        </defs>
                        {/* grid */}
                        {[0, 0.5, 1].map((t) => (
                          <line key={t} x1={padL} x2={w - padR} y1={padT + t * (h - padT - padB)} y2={padT + t * (h - padT - padB)} stroke="rgba(255,255,255,0.06)" strokeDasharray="4 4" />
                        ))}
                        {/* area cumulative */}
                        <path d={areaC} fill="url(#gradC)" stroke="none" />
                        <path d={pathC} fill="none" stroke="#f59e0b" strokeWidth={2} />
                        {/* new per bucket dotted */}
                        <path d={pathN} fill="none" stroke="#38bdf8" strokeWidth={1.5} strokeDasharray="4 3" opacity={0.9} />
                        {/* dots */}
                        {pts.map((p, i) => (
                          <circle key={i} cx={padL + i * xStep} cy={yC(p.cumulative)} r={2.5} fill="#f59e0b" />
                        ))}
                        {/* x labels - show every N */}
                        {pts.map((p, i) => {
                          const step = Math.ceil(pts.length / 8);
                          if (i % step !== 0 && i !== pts.length - 1) return null;
                          return (
                            <text key={i} x={padL + i * xStep} y={h - 6} textAnchor="middle" fontSize={9} fill="#71717a" fontFamily="monospace">
                              {p.bucket}
                            </text>
                          );
                        })}
                        {/* y labels */}
                        <text x={4} y={padT + 4} fontSize={9} fill="#71717a" fontFamily="monospace">{maxC}</text>
                        <text x={4} y={h - padB} fontSize={9} fill="#71717a" fontFamily="monospace">0</text>
                      </svg>
                      <div className="mt-2 flex items-center gap-4 text-xs font-mono">
                        <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-amber-400 inline-block" /> cumulative</span>
                        <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-sky-400 inline-block" style={{ borderTop: "2px dashed #38bdf8" }} /> new / bucket</span>
                      </div>
                    </div>
                  );
                })()}
                <div className="mt-3 max-h-40 overflow-auto rounded border border-border/30">
                  <table className="w-full text-xs font-mono">
                    <thead className="sticky top-0 bg-card">
                      <tr className="text-muted-foreground">
                        <th className="text-left px-3 py-1.5">bucket</th>
                        <th className="text-right px-3 py-1.5">new</th>
                        <th className="text-right px-3 py-1.5">cumulative</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.points.map((p) => (
                        <tr key={p.bucket} className="border-t border-border/30 hover:bg-white/5">
                          <td className="px-3 py-1">{p.bucket}</td>
                          <td className="text-right px-3 py-1 text-sky-300">+{p.new}</td>
                          <td className="text-right px-3 py-1 text-amber-300 font-bold">{p.cumulative}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : history && history.points.length === 0 && !historyLoading ? (
              <div className="mt-4 p-6 text-center text-sm text-muted-foreground border border-dashed border-border rounded-lg">
                No history yet — run <span className="font-mono text-xs">gh auth login</span> (needs stargazer timestamps) then Load again. Without auth, GitHub hides <span className="font-mono">starred_at</span>.
              </div>
            ) : !history && !historyLoading ? (
              <div className="mt-3 text-xs text-muted-foreground">Load to see star trajectory. Without auth you’ll see the note above; with auth you get month/week/day buckets.</div>
            ) : null}
          </div>

          {/* Per-repo lookup */}
          <div className="rounded-xl border border-border bg-card/50 p-5">
            <h2 className="text-sm font-bold flex items-center gap-2">
              <Search size={14} className="text-muted-foreground" /> Per-repo
              lookup
            </h2>
            <div className="mt-3 flex items-center gap-2">
              <input
                data-testid="stars-per-repo-input"
                className="flex-1 bg-background border border-border rounded-md px-3 py-1.5 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-amber-500/30"
                placeholder="repo name or owner/repo (e.g. inkscape-mcp)"
                value={perRepoQuery}
                onChange={(e) => setPerRepoQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && fetchPerRepo()}
              />
              <button
                type="button"
                data-testid="stars-per-repo-go"
                onClick={fetchPerRepo}
                disabled={perRepoLoading || !perRepoQuery.trim()}
                className="px-4 py-1.5 rounded-md bg-white text-black text-sm font-semibold hover:bg-zinc-200 disabled:opacity-50 transition-colors"
              >
                {perRepoLoading ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  "Check"
                )}
              </button>
            </div>
            {perRepoResult && (
              <div className="mt-4 rounded-lg border border-amber-500/20 bg-amber-500/5 p-4 flex items-start justify-between gap-4">
                <div>
                  <div className="font-mono text-sm font-bold flex items-center gap-2">
                    {perRepoResult.name}
                    <a
                      href={perRepoResult.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <ExternalLink size={12} />
                    </a>
                  </div>
                  {perRepoResult.description && (
                    <div className="text-xs text-muted-foreground mt-1">
                      {perRepoResult.description}
                    </div>
                  )}
                  <div className="flex items-center gap-3 mt-2 text-xs font-mono">
                    <span className="inline-flex items-center gap-1 text-amber-400">
                      <Star size={12} /> {perRepoResult.stargazerCount}
                    </span>
                    <span className="text-muted-foreground">
                      forks {perRepoResult.forkCount}
                    </span>
                    {perRepoResult.language && (
                      <span className="px-1.5 py-0.5 rounded bg-white/10">
                        {perRepoResult.language}
                      </span>
                    )}
                    {perRepoResult.updatedAt && (
                      <span className="text-muted-foreground">
                        {new Date(perRepoResult.updatedAt).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Leaderboard */}
          <div className="rounded-xl border border-border bg-card/50 p-5">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-sm font-bold flex items-center gap-2">
                <Crown size={14} className="text-amber-400" /> Leaderboard — top{" "}
                {data.top_repos.length}
              </h2>
              <div className="flex items-center gap-2">
                <Search size={12} className="text-muted-foreground" />
                <input
                  data-testid="stars-filter"
                  className="bg-background border border-border rounded-md px-2 py-1 text-xs font-mono w-40 focus:outline-none focus:ring-1 focus:ring-amber-500/20"
                  placeholder="filter…"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                />
              </div>
            </div>
            <div className="mt-4 grid gap-2" data-testid="stars-leaderboard">
              {filtered.map((r, idx) => (
                <div
                  key={r.name}
                  className="flex items-center gap-3 p-3 rounded-lg bg-background border border-border/50 hover:border-amber-500/20 transition-colors group"
                >
                  <span className="w-6 text-center text-xs font-mono text-muted-foreground">
                    #{idx + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-semibold truncate">
                        {r.name}
                      </span>
                      <a
                        href={r.url}
                        target="_blank"
                        rel="noreferrer"
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <ExternalLink
                          size={12}
                          className="text-muted-foreground"
                        />
                      </a>
                      {r.isPrivate && (
                        <span className="text-[10px] px-1 py-0.5 rounded bg-white/10 font-mono">
                          private
                        </span>
                      )}
                    </div>
                    {r.description && (
                      <div className="text-xs text-muted-foreground truncate">
                        {r.description}
                      </div>
                    )}
                  </div>
                  <div className="w-28">
                    <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <div
                        className="h-full bg-amber-400 rounded-full"
                        style={{
                          width: `${(r.stargazerCount / maxStars) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                  <span className="w-16 text-right font-mono text-sm font-bold inline-flex items-center justify-end gap-1 text-amber-400">
                    <Star size={12} /> {r.stargazerCount}
                  </span>
                  <span className="w-14 text-right font-mono text-xs text-muted-foreground hidden lg:block">
                    ↗ {r.forkCount}
                  </span>
                </div>
              ))}
              {filtered.length === 0 && (
                <div className="text-center text-sm text-muted-foreground py-8">
                  No matches.
                </div>
              )}
            </div>
            <div className="mt-4 text-xs text-muted-foreground">
              Sorted by <span className="font-mono">stargazerCount</span> desc.
              Limit 50 — call{" "}
              <span className="font-mono">
                github_ops(operation=&quot;stars_summary&quot;, owner=&quot;
                {owner}&quot;, limit=100)
              </span>{" "}
              for more.
            </div>
          </div>
        </>
      ) : (
        !loading &&
        !error && (
          <div className="rounded-xl border border-border bg-card/50 p-12 text-center text-muted-foreground">
            No data — hit Refresh.
          </div>
        )
      )}

      {loading && !data && (
        <div className="flex justify-center py-16">
          <Loader2 className="animate-spin text-amber-400" size={28} />
        </div>
      )}
    </div>
  );
}
