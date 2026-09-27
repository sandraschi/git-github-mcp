import {
  BookOpen,
  CheckCircle2,
  CircleDot,
  ExternalLink,
  GitBranch,
  GitPullRequest,
  Loader2,
  MessagesSquare,
  Star,
  Tag,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { githubOps, gitOps } from "@/lib/api";

interface RepoView {
  description?: string;
  stargazerCount?: number;
  forkCount?: number;
  url?: string;
  isPrivate?: boolean;
  defaultBranchRef?: { name: string };
  repositoryTopics?: { name: string }[];
  issues?: { totalCount: number };
}

interface Row {
  number: number;
  title: string;
  url: string;
}

interface Release {
  tagName?: string;
  name?: string;
  url?: string;
  publishedAt?: string;
}

interface LocalStatus {
  branch?: string;
  has_changes?: boolean;
  total_changes?: number;
}

export function RepoDetail() {
  const { owner, repo } = useParams<{ owner: string; repo: string }>();
  const [view, setView] = useState<RepoView | null>(null);
  const [issues, setIssues] = useState<Row[]>([]);
  const [prs, setPrs] = useState<Row[]>([]);
  const [discussions, setDiscussions] = useState<
    { number: number; title: string; url: string; category: string }[]
  >([]);
  const [releases, setReleases] = useState<Release[]>([]);
  const [local, setLocal] = useState<LocalStatus | null>(null);
  const [localMissing, setLocalMissing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!owner || !repo) return;
    setLoading(true);
    setError(null);
    setLocalMissing(false);
    Promise.allSettled([
      (
        githubOps("repo_view", { owner, repo }) as Promise<{
          success: boolean;
          result?: RepoView;
          error?: string;
        }>
      ).then((d) => {
        if (d.success) setView(d.result ?? null);
        else setError(d.error ?? "repo_view failed");
      }),
      (
        githubOps("issue_list", {
          owner,
          repo,
          state: "open",
          limit: 5,
        }) as Promise<{
          success: boolean;
          result?: { issues: Row[] };
        }>
      ).then((d) => {
        if (d.success) setIssues(d.result?.issues ?? []);
      }),
      (
        githubOps("pr_list", {
          owner,
          repo,
          state: "open",
          limit: 5,
        }) as Promise<{
          success: boolean;
          result?: { prs: Row[] };
        }>
      ).then((d) => {
        if (d.success) setPrs(d.result?.prs ?? []);
      }),
      (
        githubOps("discussion_list", { owner, repo, limit: 5 }) as Promise<{
          success: boolean;
          result?: {
            discussions: {
              number: number;
              title: string;
              url: string;
              category: string;
            }[];
          };
        }>
      ).then((d) => {
        if (d.success) setDiscussions(d.result?.discussions ?? []);
      }),
      (
        githubOps("release_list", { owner, repo, limit: 3 }) as Promise<{
          success: boolean;
          result?: { releases: Release[] };
        }>
      ).then((d) => {
        if (d.success) setReleases(d.result?.releases ?? []);
      }),
      (
        gitOps("status", { repo_path: `D:/Dev/repos/${repo}` }) as Promise<{
          success: boolean;
          result?: LocalStatus;
        }>
      )
        .then((d) => {
          if (d.success && d.result) setLocal(d.result);
          else setLocalMissing(true);
        })
        .catch(() => setLocalMissing(true)),
    ]).finally(() => setLoading(false));
  }, [owner, repo]);

  useEffect(load, [load]);

  const discLink = `/discussions?owner=${owner}&repo=${repo}`;

  return (
    <div className="space-y-5 max-w-5xl" data-testid="repo-detail">
      <div
        className="flex items-center gap-2 text-xs mono"
        style={{ color: "var(--text-dim)" }}
      >
        <Link to="/repos" className="hover:underline">
          repos
        </Link>
        <span>/</span>
        <span style={{ color: "var(--text)" }}>
          {owner}/{repo}
        </span>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2
            className="animate-spin"
            size={20}
            style={{ color: "var(--green)" }}
          />
        </div>
      ) : error ? (
        <div
          className="p-6 text-center mono text-sm rounded"
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            color: "var(--amber)",
          }}
        >
          {error}
        </div>
      ) : (
        <>
          {/* Header */}
          <div
            className="rounded p-5"
            style={{
              background: "var(--bg-2)",
              border: "1px solid var(--border)",
            }}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2 min-w-0">
                <BookOpen
                  size={16}
                  style={{ color: "var(--blue)", flexShrink: 0 }}
                />
                <h1
                  className="text-xl font-bold mono truncate"
                  style={{ color: "var(--text)" }}
                >
                  {repo}
                </h1>
              </div>
              {view?.url && (
                <a
                  href={view.url}
                  target="_blank"
                  rel="noreferrer"
                  className="shrink-0"
                >
                  <ExternalLink
                    size={14}
                    style={{ color: "var(--text-dim)" }}
                  />
                </a>
              )}
            </div>
            {view?.description && (
              <p
                className="text-sm mt-1.5"
                style={{ color: "var(--text-muted)" }}
              >
                {view.description}
              </p>
            )}
            <div className="flex items-center gap-3 mt-3 flex-wrap">
              <span
                className="mono text-xs flex items-center gap-1"
                style={{ color: "var(--text-dim)" }}
              >
                <Star size={11} /> {view?.stargazerCount ?? "--"}
              </span>
              <span
                className="mono text-xs flex items-center gap-1"
                style={{ color: "var(--text-dim)" }}
              >
                <GitBranch size={11} /> forks {view?.forkCount ?? "--"}
              </span>
              {view?.defaultBranchRef && (
                <span className="hash-chip">{view.defaultBranchRef.name}</span>
              )}
              {view?.repositoryTopics?.slice(0, 6).map((t) => (
                <span
                  key={t.name}
                  className="mono text-[10px] px-1.5 py-0.5 rounded"
                  style={{
                    background: "var(--bg-3)",
                    border: "1px solid var(--border)",
                    color: "var(--text-muted)",
                  }}
                >
                  {t.name}
                </span>
              ))}
              <span
                className="mono text-xs ml-auto"
                style={{ color: "var(--text-dim)" }}
              >
                {localMissing ? (
                  "not checked out locally"
                ) : local ? (
                  <>
                    {local.branch}
                    <span
                      style={{
                        color: local.has_changes
                          ? "var(--amber)"
                          : "var(--green)",
                      }}
                    >
                      {" "}
                      · {local.total_changes} changes
                    </span>
                  </>
                ) : (
                  "local: …"
                )}
              </span>
            </div>
          </div>

          {/* KPI links */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <KpiLink
              to={`/issues?owner=${owner}&repo=${repo}`}
              icon={<CircleDot size={14} style={{ color: "var(--green)" }} />}
              label="Open issues"
              value={issues.length}
            />
            <KpiLink
              to={`/prs?owner=${owner}&repo=${repo}`}
              icon={
                <GitPullRequest size={14} style={{ color: "var(--blue)" }} />
              }
              label="Open PRs"
              value={prs.length}
            />
            <KpiLink
              to={discLink}
              icon={
                <MessagesSquare size={14} style={{ color: "var(--purple)" }} />
              }
              label="Discussions"
              value={discussions.length}
            />
            <div
              className="rounded p-4"
              style={{
                background: "var(--bg-2)",
                border: "1px solid var(--border)",
              }}
            >
              <div
                className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest"
                style={{ color: "var(--text-dim)" }}
              >
                <Tag size={12} /> Latest release
              </div>
              <div
                className="mono text-sm mt-1 truncate"
                style={{ color: "var(--text)" }}
              >
                {releases[0]?.tagName ?? releases[0]?.name ?? "--"}
              </div>
            </div>
          </div>

          {/* Lists */}
          <div className="grid gap-4 lg:grid-cols-2">
            <PreviewList
              title="Issues"
              to={`/issues?owner=${owner}&repo=${repo}`}
              rows={issues}
              empty="No open issues"
            />
            <PreviewList
              title="Pull requests"
              to={`/prs?owner=${owner}&repo=${repo}`}
              rows={prs}
              empty="No open PRs"
            />
          </div>
          <PreviewList
            title="Discussions"
            to={discLink}
            rows={discussions.map((d) => ({
              ...d,
              title: `[${d.category}] ${d.title}`,
            }))}
            empty="No discussions — start one"
          />
        </>
      )}
    </div>
  );
}

function KpiLink({
  to,
  icon,
  label,
  value,
}: {
  to: string;
  icon: React.ReactNode;
  label: string;
  value: number | string;
}) {
  return (
    <Link
      to={to}
      className="rounded p-4 hover:border-slate-600 transition-colors block"
      style={{ background: "var(--bg-2)", border: "1px solid var(--border)" }}
      data-testid={`repo-kpi-${label.replace(/\s+/g, "-").toLowerCase()}`}
    >
      <div
        className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest"
        style={{ color: "var(--text-dim)" }}
      >
        {icon} {label}
      </div>
      <div className="mono text-xl mt-1" style={{ color: "var(--text)" }}>
        {value}
      </div>
    </Link>
  );
}

function PreviewList({
  title,
  to,
  rows,
  empty,
}: {
  title: string;
  to: string;
  rows: Row[];
  empty: string;
}) {
  return (
    <div
      className="rounded overflow-hidden"
      style={{ border: "1px solid var(--border)", background: "var(--bg-2)" }}
    >
      <div
        className="px-4 py-2.5 flex items-center justify-between"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <span
          className="text-xs font-bold uppercase tracking-widest"
          style={{ color: "var(--text-muted)" }}
        >
          {title}
        </span>
        <Link
          to={to}
          className="mono text-xs hover:underline"
          style={{ color: "var(--blue)" }}
        >
          open
        </Link>
      </div>
      {rows.length === 0 ? (
        <div className="p-4 text-xs" style={{ color: "var(--text-dim)" }}>
          {empty}
        </div>
      ) : (
        rows.map((r) => (
          <div
            key={r.number}
            className="px-4 py-2 flex items-center gap-2"
            style={{ borderBottom: "1px solid var(--border)" }}
          >
            <CheckCircle2
              size={11}
              style={{ color: "var(--text-dim)", flexShrink: 0 }}
            />
            <a
              href={r.url}
              target="_blank"
              rel="noreferrer"
              className="text-xs truncate hover:underline"
              style={{ color: "var(--text)" }}
            >
              #{r.number} {r.title}
            </a>
          </div>
        ))
      )}
    </div>
  );
}
