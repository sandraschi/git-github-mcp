import {
  CircleDot,
  GitPullRequest,
  Inbox,
  Loader2,
  RefreshCw,
  Ship,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { githubOps } from "@/lib/api";

const FLEET_KEY = "git-github-mcp-inbox-fleet";

interface PRRow {
  number: number;
  title: string;
  state: string;
  url: string;
  author: { login: string };
  headRefName: string;
  baseRefName: string;
  isDraft: boolean;
  createdAt: string;
  updatedAt?: string;
  comments?: number;
  repoSlug: string;
}

interface IssueRow {
  number: number;
  title: string;
  state: string;
  url: string;
  author: { login: string };
  labels: { name: string; color: string }[];
  createdAt: string;
  updatedAt?: string;
  repoSlug: string;
}

function parseFleet(text: string): { owner: string; repo: string }[] {
  const out: { owner: string; repo: string }[] = [];
  for (const line of text.split(/\r?\n/)) {
    const t = line.trim();
    if (!t || t.startsWith("#")) continue;
    const m = t.match(/^([\w.-]+)\/([\w.-]+)$/);
    if (m) out.push({ owner: m[1], repo: m[2] });
  }
  return out;
}

function staleDays(iso: string | undefined): number | null {
  if (!iso) return null;
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return null;
  return Math.floor((Date.now() - t) / (86400 * 1000));
}

export function InboxPage() {
  const [tab, setTab] = useState<"prs" | "issues">("prs");
  const [fleetMode, setFleetMode] = useState(false);
  const [fleetText, setFleetText] = useState(() => {
    try {
      return (
        localStorage.getItem(FLEET_KEY) ??
        "sandraschi/git-github-mcp\nsandraschi/pywinauto-mcp"
      );
    } catch {
      return "sandraschi/git-github-mcp\nsandraschi/pywinauto-mcp";
    }
  });
  const [owner, setOwner] = useState("sandraschi");
  const [repo, setRepo] = useState("git-github-mcp");
  const [state, setState] = useState<"open" | "closed">("open");
  const [prs, setPrs] = useState<PRRow[]>([]);
  const [issues, setIssues] = useState<IssueRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const slugs = useMemo(() => {
    if (fleetMode) return parseFleet(fleetText);
    if (owner.trim() && repo.trim())
      return [{ owner: owner.trim(), repo: repo.trim() }];
    return [];
  }, [fleetMode, fleetText, owner, repo]);

  const loadPrs = useCallback(async () => {
    if (slugs.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      const rows: PRRow[] = [];
      for (const { owner: o, repo: r } of slugs) {
        const d = (await githubOps("pr_list", {
          owner: o,
          repo: r,
          state,
          limit: 50,
        })) as { success: boolean; result?: { prs: PRRow[] }; error?: string };
        if (!d.success) throw new Error(d.error ?? "pr_list failed");
        const list = d.result?.prs ?? [];
        for (const p of list) {
          rows.push({
            ...p,
            repoSlug: `${o}/${r}`,
          });
        }
      }
      rows.sort((a, b) => {
        const ua = new Date(a.updatedAt ?? a.createdAt).getTime();
        const ub = new Date(b.updatedAt ?? b.createdAt).getTime();
        return ub - ua;
      });
      setPrs(rows);
    } catch (e) {
      setError(String(e));
      setPrs([]);
    } finally {
      setLoading(false);
    }
  }, [slugs, state]);

  const loadIssues = useCallback(async () => {
    if (slugs.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      const rows: IssueRow[] = [];
      for (const { owner: o, repo: r } of slugs) {
        const d = (await githubOps("issue_list", {
          owner: o,
          repo: r,
          state,
          limit: 50,
        })) as {
          success: boolean;
          result?: { issues: IssueRow[] };
          error?: string;
        };
        if (!d.success) throw new Error(d.error ?? "issue_list failed");
        const list = d.result?.issues ?? [];
        for (const it of list) {
          rows.push({ ...it, repoSlug: `${o}/${r}` });
        }
      }
      rows.sort((a, b) => {
        const ua = new Date(a.updatedAt ?? a.createdAt).getTime();
        const ub = new Date(b.updatedAt ?? b.createdAt).getTime();
        return ub - ua;
      });
      setIssues(rows);
    } catch (e) {
      setError(String(e));
      setIssues([]);
    } finally {
      setLoading(false);
    }
  }, [slugs, state]);

  const load = useCallback(() => {
    if (tab === "prs") return loadPrs();
    return loadIssues();
  }, [tab, loadPrs, loadIssues]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    try {
      localStorage.setItem(FLEET_KEY, fleetText);
    } catch {
      /* ignore */
    }
  }, [fleetText]);

  return (
    <div className="space-y-4 max-w-5xl">
      <div className="flex items-start gap-3">
        <Inbox className="h-8 w-8 shrink-0 text-blue-400 mt-1" />
        <div>
          <h1 className="text-2xl font-bold text-slate-100">
            Pull requests &amp; Issues
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-3xl">
            Human triage view for the same operations as{" "}
            <code className="text-slate-300">github_ops(pr_list)</code> /{" "}
            <code className="text-slate-300">issue_list</code>. A{" "}
            <strong className="text-slate-200">supervisor</strong> (OpenClaw,
            OpenManus, RoboFang, OpenClaude, etc.) can run a daily heartbeat
            that lists open PRs/issues across your repo fleet — this page is the
            dashboard for the same data. For the scheduled{" "}
            <a href="/breakfast" className="text-amber-300 hover:underline">
              breakfast runner
            </a>{" "}
            digest, use <strong className="text-slate-200">Breakfast</strong> in
            the sidebar.
          </p>
        </div>
      </div>

      <div
        className="rounded-lg border border-slate-700 bg-slate-900/40 p-3 text-xs text-slate-400 flex gap-2 items-start"
        role="note"
      >
        <Ship className="h-4 w-4 shrink-0 text-amber-500 mt-0.5" />
        <span>
          <strong className="text-slate-300">Agentic prompt idea:</strong>{" "}
          &quot;Using github_ops, list open PRs for each repo in our fleet (see
          fleet list), summarize anything with no maintainer reply in 7+ days,
          and draft a short acknowledgment comment.&quot;
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {(["prs", "issues"] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              tab === t
                ? "bg-blue-600/20 text-blue-300 border border-blue-500/40"
                : "bg-slate-800/60 text-slate-400 border border-slate-700 hover:text-slate-200"
            }`}
          >
            {t === "prs" ? (
              <GitPullRequest className="h-4 w-4" />
            ) : (
              <CircleDot className="h-4 w-4" />
            )}
            {t === "prs" ? "Pull requests" : "Issues"}
          </button>
        ))}
        <span className="text-slate-600">|</span>
        <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
          <input
            type="checkbox"
            checked={fleetMode}
            onChange={(e) => setFleetMode(e.target.checked)}
            className="rounded border-slate-600"
          />
          Fleet (multi-repo)
        </label>
        {(["open", "closed"] as const).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setState(s)}
            className={`px-2.5 py-1 rounded text-xs ${
              state === s
                ? "bg-slate-700 text-white"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {s}
          </button>
        ))}
        <button
          type="button"
          onClick={load}
          className="ml-auto p-2 rounded border border-slate-600 text-slate-400 hover:text-white"
          title="Refresh"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {fleetMode ? (
        <div className="space-y-2">
          <label
            htmlFor="fleet-repos-textarea"
            className="block text-xs text-slate-500 uppercase tracking-wide"
          >
            One owner/repo per line
          </label>
          <textarea
            id="fleet-repos-textarea"
            className="w-full min-h-[100px] rounded-md border border-slate-700 bg-slate-950/80 px-3 py-2 font-mono text-sm text-slate-200"
            value={fleetText}
            onChange={(e) => setFleetText(e.target.value)}
            placeholder="sandraschi/repo-one&#10;sandraschi/repo-two"
          />
        </div>
      ) : (
        <div className="flex items-center gap-2 flex-wrap">
          <input
            className="mono text-xs px-3 py-1.5 rounded outline-none w-36 bg-slate-900 border border-slate-700 text-slate-200"
            value={owner}
            onChange={(e) => setOwner(e.target.value)}
            placeholder="owner"
          />
          <span className="text-slate-600">/</span>
          <input
            className="mono text-xs px-3 py-1.5 rounded outline-none flex-1 min-w-[120px] bg-slate-900 border border-slate-700 text-slate-200"
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
            placeholder="repo"
          />
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="animate-spin h-8 w-8 text-blue-500" />
        </div>
      ) : error ? (
        <div className="p-4 rounded border border-amber-900/50 bg-amber-950/30 text-amber-200 text-sm font-mono">
          {error} — ensure <span className="text-white">gh auth login</span> and
          API is running.
        </div>
      ) : tab === "prs" ? (
        <div className="rounded-lg border border-slate-800 overflow-hidden">
          {prs.length === 0 ? (
            <div className="p-10 text-center text-slate-500 text-sm">
              No {state} pull requests
            </div>
          ) : (
            prs.map((pr) => {
              const sd = staleDays(pr.updatedAt ?? pr.createdAt);
              const stale = sd !== null && sd >= 7;
              return (
                <div
                  key={`${pr.repoSlug}-${pr.number}`}
                  className="flex items-start gap-3 px-4 py-3 border-b border-slate-800/80 last:border-0 hover:bg-white/[0.02]"
                >
                  <GitPullRequest
                    className="h-4 w-4 mt-0.5 shrink-0"
                    style={{
                      color: pr.isDraft
                        ? "#64748b"
                        : pr.state === "open"
                          ? "#22c55e"
                          : "#a78bfa",
                    }}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                        {pr.repoSlug}
                      </span>
                      {stale && (
                        <span className="text-xs text-amber-400 border border-amber-700/50 rounded px-1.5 py-0">
                          {sd}d since activity
                        </span>
                      )}
                    </div>
                    <a
                      href={pr.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm font-medium text-slate-100 hover:underline block truncate mt-1"
                    >
                      {pr.title}
                      {pr.isDraft && (
                        <span className="ml-2 text-xs text-slate-500 border border-slate-600 rounded px-1">
                          Draft
                        </span>
                      )}
                    </a>
                    <div className="flex flex-wrap gap-2 mt-1 text-xs text-slate-500">
                      <span>#{pr.number}</span>
                      <span>{pr.author?.login}</span>
                      {typeof pr.comments === "number" && (
                        <span>{pr.comments} comments</span>
                      )}
                      <span className="font-mono text-slate-600">
                        {pr.headRefName} → {pr.baseRefName}
                      </span>
                    </div>
                  </div>
                  <div className="text-right text-xs text-slate-500 shrink-0">
                    <div>{new Date(pr.createdAt).toLocaleDateString()}</div>
                    {pr.updatedAt && (
                      <div className="text-slate-600 mt-0.5">
                        upd {new Date(pr.updatedAt).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      ) : (
        <div className="rounded-lg border border-slate-800 overflow-hidden">
          {issues.length === 0 ? (
            <div className="p-10 text-center text-slate-500 text-sm">
              No {state} issues
            </div>
          ) : (
            issues.map((iss) => {
              const sd = staleDays(iss.updatedAt ?? iss.createdAt);
              const stale = sd !== null && sd >= 7;
              return (
                <div
                  key={`${iss.repoSlug}-${iss.number}`}
                  className="flex items-start gap-3 px-4 py-3 border-b border-slate-800/80 last:border-0 hover:bg-white/[0.02]"
                >
                  <CircleDot
                    className="h-4 w-4 mt-0.5 shrink-0"
                    style={{
                      color: iss.state === "open" ? "#22c55e" : "#a78bfa",
                    }}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                        {iss.repoSlug}
                      </span>
                      {stale && (
                        <span className="text-xs text-amber-400 border border-amber-700/50 rounded px-1.5 py-0">
                          {sd}d since activity
                        </span>
                      )}
                    </div>
                    <a
                      href={iss.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm font-medium text-slate-100 hover:underline block truncate mt-1"
                    >
                      {iss.title}
                    </a>
                    <div className="flex flex-wrap gap-2 mt-1 text-xs text-slate-500">
                      <span>#{iss.number}</span>
                      <span>{iss.author?.login}</span>
                      {iss.labels?.map((l) => (
                        <span
                          key={l.name}
                          className="px-1.5 py-0 rounded"
                          style={{
                            background: `#${l.color}22`,
                            color: `#${l.color}`,
                            border: `1px solid #${l.color}44`,
                          }}
                        >
                          {l.name}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="text-right text-xs text-slate-500 shrink-0">
                    <div>{new Date(iss.createdAt).toLocaleDateString()}</div>
                    {iss.updatedAt && (
                      <div className="text-slate-600 mt-0.5">
                        upd {new Date(iss.updatedAt).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
