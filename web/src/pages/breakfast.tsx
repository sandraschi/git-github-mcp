import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Bell,
  CircleDot,
  Coffee,
  ExternalLink,
  GitPullRequest,
  Loader2,
  Play,
  RefreshCw,
} from 'lucide-react';
import { runMorningDigest } from '@/lib/api';

const FLEET_KEY = 'git-github-mcp-inbox-fleet';
const LAST_DIGEST_KEY = 'git-github-mcp-breakfast-last';

type RunnerStatus = 'idle' | 'running' | 'done' | 'error';

type Author = { login?: string };

type DigestPr = {
  number: number;
  title: string;
  state: string;
  url: string;
  author?: Author;
  headRefName?: string;
  baseRefName?: string;
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
  labels?: { name: string; color?: string }[];
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

type DigestResponse = {
  success: boolean;
  result?: DigestResult;
  error?: string;
  message?: string;
  recovery_options?: string[];
};

function parseFleet(text: string): string {
  return text
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l && !l.startsWith('#'))
    .join('\n');
}

function relTime(iso: string | undefined): string {
  if (!iso) return '';
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return '';
  const days = Math.floor((Date.now() - t) / 86400000);
  if (days === 0) return 'today';
  if (days === 1) return '1d ago';
  return `${days}d ago`;
}

function loadCachedDigest(): DigestResult | null {
  try {
    const raw = localStorage.getItem(LAST_DIGEST_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as DigestResult;
  } catch {
    return null;
  }
}

export function BreakfastPage() {
  const [fleetText, setFleetText] = useState(() => {
    try {
      return localStorage.getItem(FLEET_KEY) ?? 'sandraschi/git-github-mcp\nsandraschi/scraper-mcp';
    } catch {
      return 'sandraschi/git-github-mcp';
    }
  });
  const [staleDays, setStaleDays] = useState(7);
  const [sinceLastRun, setSinceLastRun] = useState(true);
  const [deliverFile, setDeliverFile] = useState(true);
  const [deliverAiwatcher, setDeliverAiwatcher] = useState(false);
  const [tab, setTab] = useState<'notifications' | 'prs' | 'issues' | 'repos'>('notifications');
  const [data, setData] = useState<DigestResult | null>(() => loadCachedDigest());
  const [status, setStatus] = useState<RunnerStatus>(() => (loadCachedDigest() ? 'done' : 'idle'));
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);

  const run = useCallback(async () => {
    const fleet = parseFleet(fleetText);
    if (!fleet) {
      setError('Add at least one owner/repo line to the fleet list.');
      setStatus('error');
      return;
    }
    setStatus('running');
    setError(null);
    setLastMessage(null);
    try {
      const deliverParts: string[] = [];
      if (deliverFile) deliverParts.push('file');
      if (deliverAiwatcher) deliverParts.push('aiwatcher');

      const res = (await runMorningDigest({
        fleet_repos: fleet,
        stale_days: staleDays,
        include_issues: true,
        include_notifications: true,
        since_last_run: sinceLastRun,
        deliver: deliverParts.length > 0 ? deliverParts.join(',') : undefined,
      })) as DigestResponse;
      if (!res.success) {
        throw new Error(res.error ?? 'Digest failed');
      }
      const result = res.result ?? null;
      setData(result);
      setLastMessage(res.message ?? 'Runner finished');
      setStatus('done');
      if (result) {
        try {
          localStorage.setItem(LAST_DIGEST_KEY, JSON.stringify(result));
        } catch {
          /* ignore */
        }
      }
    } catch (e) {
      setError(String(e));
      setStatus('error');
    }
  }, [fleetText, staleDays, sinceLastRun, deliverFile, deliverAiwatcher]);

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
  const running = status === 'running';

  const statusLabel: Record<RunnerStatus, string> = {
    idle: 'Ready — press Start runner',
    running: 'Running fleet scan…',
    done: 'Last run complete',
    error: 'Run failed',
  };

  const statusColor: Record<RunnerStatus, string> = {
    idle: 'bg-slate-700 text-slate-300',
    running: 'bg-amber-500/20 text-amber-200 border-amber-500/40',
    done: 'bg-emerald-500/20 text-emerald-200 border-emerald-500/40',
    error: 'bg-red-500/20 text-red-200 border-red-500/40',
  };

  return (
    <div className="space-y-5 max-w-5xl">
      <div className="flex items-start gap-3">
        <Coffee className="h-8 w-8 shrink-0 text-amber-400 mt-1" />
        <div>
          <h1 className="text-2xl font-bold text-foreground">Breakfast runner</h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
            On-demand fleet digest — GitHub notifications, open PRs/issues, stale threads.
            Equivalent to <code className="text-foreground/80">fleet_morning_digest</code>.
          </p>
        </div>
      </div>

      {/* Runner control panel */}
      <section className="rounded-xl border border-border bg-card/60 p-4 md:p-5 space-y-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span
              className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold border ${statusColor[status]}`}
            >
              {running && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              {statusLabel[status]}
            </span>
            {data?.generated_at && status !== 'running' && (
              <span className="text-xs text-muted-foreground font-mono">
                {new Date(data.generated_at).toLocaleString()}
                {data.maintainer ? ` · ${data.maintainer}` : ''}
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
              {running ? 'Running…' : 'Start runner'}
            </button>
            {data && !running && (
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

        {lastMessage && status === 'done' && (
          <p className="text-sm text-emerald-400/90">{lastMessage}</p>
        )}

        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <label className="text-xs text-muted-foreground uppercase tracking-wide">Fleet repos</label>
            <textarea
              className="mt-1 w-full min-h-[88px] rounded-md border border-border bg-background/80 px-3 py-2 font-mono text-sm"
              value={fleetText}
              onChange={(e) => setFleetText(e.target.value)}
              placeholder="sandraschi/git-github-mcp"
              disabled={running}
            />
            <p className="text-[11px] text-muted-foreground mt-1">Shared with /inbox · one owner/repo per line</p>
          </div>
          <div className="space-y-3">
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
            Ensure <span className="font-mono text-white">gh auth login</span> and backend on port 10702.
          </p>
        </div>
      )}

      {!data && status === 'idle' && !error && (
        <div className="rounded-lg border border-dashed border-border p-12 text-center text-muted-foreground text-sm">
          No results yet. Configure your fleet list and click <strong className="text-foreground">Start runner</strong>.
        </div>
      )}

      {totals && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {[
            { label: 'Notifications', value: totals.notifications, accent: 'text-rose-400' },
            { label: 'Open PRs', value: totals.open_prs, accent: 'text-emerald-400' },
            { label: 'Open issues', value: totals.open_issues, accent: 'text-sky-400' },
            { label: 'Stale PRs', value: totals.stale_prs, accent: 'text-amber-400' },
            { label: 'Stale issues', value: totals.stale_issues, accent: 'text-amber-400' },
          ].map((c) => (
            <div key={c.label} className="rounded-lg border border-border bg-card/40 px-3 py-2 text-center">
              <div className={`text-xl font-semibold ${c.accent}`}>{c.value}</div>
              <div className="text-xs text-muted-foreground">{c.label}</div>
            </div>
          ))}
        </div>
      )}

      {data && (
        <>
          <div className="flex flex-wrap items-center gap-2">
            {(
              [
                ['notifications', 'New activity', Bell],
                ['prs', 'Pull requests', GitPullRequest],
                ['issues', 'Issues', CircleDot],
                ['repos', 'Repos', ExternalLink],
              ] as const
            ).map(([id, label, Icon]) => (
              <button
                key={id}
                type="button"
                onClick={() => setTab(id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors border ${
                  tab === id
                    ? 'bg-amber-500/15 text-amber-200 border-amber-500/35'
                    : 'bg-card/60 text-muted-foreground border-border hover:text-foreground'
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
          ) : tab === 'notifications' ? (
            <ItemList
              empty="No new notifications since last digest run."
              items={notifications.map((n, i) => ({
                key: `n-${i}`,
                repo: n.repository ?? 'GitHub',
                repoUrl: n.repository ? `https://github.com/${n.repository}` : undefined,
                title: n.subject_title ?? n.title ?? 'Notification',
                url: n.subject_url ?? '',
                meta: [n.reason, n.unread ? 'unread' : 'read', relTime(n.updated_at)].filter(Boolean).join(' · '),
                stale: Boolean(n.unread),
              }))}
            />
          ) : tab === 'prs' ? (
            <ItemList
              empty="No open pull requests in fleet."
              items={(data.open_prs ?? []).map((pr) => ({
                key: `${pr.repo_slug}-${pr.number}`,
                repo: pr.repo_slug,
                repoUrl: pr.repo_url,
                title: pr.title,
                url: pr.url,
                meta: [
                  `#${pr.number}`,
                  pr.author?.login,
                  pr.isDraft ? 'draft' : null,
                  typeof pr.comments === 'number' ? `${pr.comments} comments` : null,
                  relTime(pr.updatedAt ?? pr.createdAt),
                ]
                  .filter(Boolean)
                  .join(' · '),
                stale: pr.is_stale,
                staleReason: pr.stale_reason,
              }))}
            />
          ) : tab === 'issues' ? (
            <ItemList
              empty="No open issues in fleet."
              items={(data.open_issues ?? []).map((iss) => ({
                key: `${iss.repo_slug}-${iss.number}`,
                repo: iss.repo_slug,
                repoUrl: iss.repo_url,
                title: iss.title,
                url: iss.url,
                meta: [`#${iss.number}`, iss.author?.login, relTime(iss.updatedAt ?? iss.createdAt)]
                  .filter(Boolean)
                  .join(' · '),
                stale: iss.is_stale,
                staleReason: iss.stale_reason,
              }))}
            />
          ) : (
            <div className="rounded-lg border border-border overflow-hidden">
              {(data.repo_links ?? []).length === 0 ? (
                <div className="p-10 text-center text-muted-foreground text-sm">No repos scanned</div>
              ) : (
                (data.repo_links ?? []).map((r) => (
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
                ))
              )}
            </div>
          )}

          {(data.repo_errors?.length ?? 0) > 0 && (
            <div className="text-xs text-amber-400/90 font-mono border border-amber-900/40 rounded p-3 bg-amber-950/20">
              {data.repo_errors?.map((e) => (
                <div key={e}>{e}</div>
              ))}
            </div>
          )}
        </>
      )}
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
    return (
      <div className="p-10 text-center text-muted-foreground text-sm rounded-lg border border-border">{empty}</div>
    );
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
                <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-muted">{row.repo}</span>
              )}
              {row.stale && (
                <span className="text-xs text-amber-400 border border-amber-700/50 rounded px-1.5 py-0">
                  {row.staleReason ?? 'needs attention'}
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
              <span className="text-sm font-medium block truncate mt-1">{row.title}</span>
            )}
            <div className="text-xs text-muted-foreground mt-1">{row.meta}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
