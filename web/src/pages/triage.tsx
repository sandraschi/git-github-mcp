import { AlertOctagon, Loader2, RefreshCw, Send, XCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { githubOps, runMorningDigest } from "@/lib/api";
import {
  assess,
  type TriageAssessment,
  type TriageBucket,
  type TriageGrade,
} from "@/lib/triage-grade";

const FLEET_KEY = "git-github-mcp-triage-fleet";
const DEFAULT_FLEET =
  "sandraschi/inkscape-mcp\nsandraschi/windows-computer-use-mcp";
const PAGE_SIZE = 20;

type RowKind = "issue" | "pr";

interface TriageRow {
  key: string;
  slug: string;
  owner: string;
  repo: string;
  kind: RowKind;
  number: number;
  title: string;
  url: string;
  author: string;
  createdAt: string;
  reason: string;
  bucket: TriageBucket;
  commentCount: number;
}

interface DetailState {
  loading: boolean;
  body?: string;
  assessment?: TriageAssessment;
  error?: string;
}

interface DigestEnvelope {
  success: boolean;
  result?: {
    all_needs_reply?: Record<string, unknown>[];
    all_stale_issues?: Record<string, unknown>[];
    all_stale_prs?: Record<string, unknown>[];
    totals?: {
      needs_reply?: number;
      stale_issues?: number;
      stale_prs?: number;
    };
  };
  error?: string;
}

const str = (v: unknown, fallback = ""): string =>
  typeof v === "string" ? v : fallback;
const num = (v: unknown, fallback = 0): number =>
  typeof v === "number" ? v : fallback;

function splitSlug(slug: string): [string, string] {
  const [owner, ...rest] = slug.split("/");
  return [owner ?? "", rest.join("/")];
}

function rowsFromDigest(env: DigestEnvelope): TriageRow[] {
  const out: TriageRow[] = [];
  const res = env.result ?? {};
  for (const raw of res.all_needs_reply ?? []) {
    const slug = str(raw.slug ?? raw.repo_slug);
    const [owner, repo] = splitSlug(slug);
    const kind = (raw.kind === "pr" ? "pr" : "issue") as RowKind;
    const number = num(raw.number);
    out.push({
      key: `nr-${slug}-${kind}-${number}`,
      slug,
      owner,
      repo,
      kind,
      number,
      title: str(raw.title),
      url: str(raw.url),
      author: str((raw.author as { login?: string } | undefined)?.login, "?"),
      createdAt: str(raw.createdAt),
      reason: str(raw.need_reply_reason, "no reply yet"),
      bucket: "needs_reply",
      commentCount: num(
        raw.comment_count,
        typeof raw.comments === "number" ? raw.comments : -1,
      ),
    });
  }
  for (const raw of res.all_stale_issues ?? []) {
    const slug = str(raw.slug ?? raw.repo_slug);
    const [owner, repo] = splitSlug(slug);
    const number = num(raw.number);
    out.push({
      key: `st-issue-${slug}-${number}`,
      slug,
      owner,
      repo,
      kind: "issue",
      number,
      title: str(raw.title),
      url: str(raw.url),
      author: str((raw.author as { login?: string } | undefined)?.login, "?"),
      createdAt: str(raw.createdAt),
      reason: str(raw.stale_reason, "stale"),
      bucket: "stale",
      commentCount: num(
        raw.comment_count,
        typeof raw.comments === "number" ? raw.comments : -1,
      ),
    });
  }
  for (const raw of res.all_stale_prs ?? []) {
    const slug = str(raw.slug ?? raw.repo_slug);
    const [owner, repo] = splitSlug(slug);
    const number = num(raw.number);
    out.push({
      key: `st-pr-${slug}-${number}`,
      slug,
      owner,
      repo,
      kind: "pr",
      number,
      title: str(raw.title),
      url: str(raw.url),
      author: str((raw.author as { login?: string } | undefined)?.login, "?"),
      createdAt: str(raw.createdAt),
      reason: str(raw.stale_reason, "stale"),
      bucket: "stale",
      commentCount: num(
        raw.comment_count,
        typeof raw.comments === "number" ? raw.comments : -1,
      ),
    });
  }
  return out;
}

function relTime(iso: string): string {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "";
  const days = Math.floor((Date.now() - t) / 86400000);
  if (days <= 0) return "today";
  if (days === 1) return "1d ago";
  return `${days}d ago`;
}

const GRADE_STYLE: Record<
  TriageGrade,
  { color: string; border: string; bg: string }
> = {
  A: { color: "var(--green)", border: "var(--green-dim)", bg: "transparent" },
  B: { color: "var(--cyan)", border: "var(--cyan)", bg: "transparent" },
  C: { color: "var(--amber)", border: "var(--amber)", bg: "transparent" },
  D: { color: "var(--red)", border: "var(--red)", bg: "transparent" },
};

export function Triage() {
  const [fleetText, setFleetText] = useState(() => {
    try {
      return localStorage.getItem(FLEET_KEY) ?? DEFAULT_FLEET;
    } catch {
      return DEFAULT_FLEET;
    }
  });
  const [staleDays, setStaleDays] = useState(7);
  const [rows, setRows] = useState<TriageRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ranAt, setRanAt] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [bucketFilter, setBucketFilter] = useState<"all" | TriageBucket>("all");
  const [kindFilter, setKindFilter] = useState<"all" | RowKind>("all");
  const [gradeFilter, setGradeFilter] = useState<
    "all" | TriageGrade | "ungraded"
  >("all");
  const [sort, setSort] = useState<"oldest" | "newest">("oldest");
  const [page, setPage] = useState(1);

  const [details, setDetails] = useState<Record<string, DetailState>>({});
  const [replies, setReplies] = useState<Record<string, string>>({});
  const [acting, setActing] = useState<Record<string, boolean>>({});
  const [acted, setActed] = useState<Record<string, string>>({});

  useEffect(() => {
    try {
      localStorage.setItem(FLEET_KEY, fleetText);
    } catch {
      /* ignore */
    }
  }, [fleetText]);

  const resettable =
    <T,>(setter: (v: T) => void) =>
    (v: T) => {
      setter(v);
      setPage(1);
    };

  const setSearchPage = resettable(setSearch);
  const setBucketPage = resettable(setBucketFilter);
  const setKindPage = resettable(setKindFilter);
  const setGradePage = resettable(setGradeFilter);
  const setSortPage = resettable(setSort);

  const run = async () => {
    const fleet = fleetText
      .split(/\r?\n/)
      .map((l) => l.trim())
      .filter((l) => l && !l.startsWith("#"))
      .join("\n");
    if (!fleet) {
      setError("Add at least one owner/repo line.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const env = (await runMorningDigest({
        fleet_repos: fleet,
        stale_days: staleDays,
        include_issues: true,
        include_notifications: false,
        include_discussions: false,
        include_local: false,
        limit_per_repo: 30,
      })) as DigestEnvelope;
      if (!env.success) throw new Error(env.error ?? "Digest failed");
      setRows(rowsFromDigest(env));
      setDetails({});
      setPage(1);
      setRanAt(new Date().toLocaleString());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const toggleDetail = async (row: TriageRow) => {
    if (details[row.key] && !details[row.key].loading) {
      setDetails((d) => {
        const next = { ...d };
        delete next[row.key];
        return next;
      });
      return;
    }
    setDetails((d) => ({ ...d, [row.key]: { loading: true } }));
    try {
      const op = row.kind === "issue" ? "issue_view" : "pr_view";
      const idArg =
        row.kind === "issue"
          ? { issue_number: row.number }
          : { pr_number: row.number };
      const res = (await githubOps(op, {
        owner: row.owner,
        repo: row.repo,
        ...idArg,
      })) as {
        success: boolean;
        result?: Record<string, unknown>;
        error?: string;
      };
      if (!res.success) throw new Error(res.error ?? "Fetch failed");
      const body = str(res.result?.body ?? res.result?.description);
      const assessment = assess(
        row.bucket,
        row.kind,
        row.title,
        body,
        row.slug,
        row.number,
      );
      setDetails((d) => ({
        ...d,
        [row.key]: { loading: false, body, assessment },
      }));
      setReplies((r) =>
        r[row.key] === undefined
          ? { ...r, [row.key]: assessment.suggestedReply }
          : r,
      );
    } catch (e) {
      setDetails((d) => ({
        ...d,
        [row.key]: {
          loading: false,
          error: e instanceof Error ? e.message : String(e),
        },
      }));
    }
  };

  const postReply = async (row: TriageRow) => {
    const body = (replies[row.key] ?? "").trim();
    if (!body) return;
    const op = row.kind === "issue" ? "issue_comment" : "pr_comment";
    const idArg =
      row.kind === "issue"
        ? { issue_number: row.number }
        : { pr_number: row.number };
    setActing((a) => ({ ...a, [row.key]: true }));
    try {
      const res = (await githubOps(op, {
        owner: row.owner,
        repo: row.repo,
        ...idArg,
        body,
      })) as { success: boolean; error?: string };
      if (!res.success) throw new Error(res.error ?? "Post failed");
      setActed((a) => ({ ...a, [row.key]: "replied" }));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setActing((a) => ({ ...a, [row.key]: false }));
    }
  };

  const closeRow = async (row: TriageRow) => {
    const op = row.kind === "issue" ? "issue_close" : "pr_close";
    const idArg =
      row.kind === "issue"
        ? { issue_number: row.number }
        : { pr_number: row.number };
    setActing((a) => ({ ...a, [row.key]: true }));
    try {
      const res = (await githubOps(op, {
        owner: row.owner,
        repo: row.repo,
        ...idArg,
      })) as { success: boolean; error?: string };
      if (!res.success) throw new Error(res.error ?? "Close failed");
      setActed((a) => ({ ...a, [row.key]: "closed" }));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setActing((a) => ({ ...a, [row.key]: false }));
    }
  };

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    let list = rows.filter((r) => {
      if (bucketFilter !== "all" && r.bucket !== bucketFilter) return false;
      if (kindFilter !== "all" && r.kind !== kindFilter) return false;
      if (q) {
        const hay =
          `${r.title} ${r.slug} ${r.author} #${r.number}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      if (gradeFilter !== "all") {
        const g = details[r.key]?.assessment?.grade;
        if (gradeFilter === "ungraded") {
          if (g !== undefined) return false;
        } else if (g !== gradeFilter) {
          return false;
        }
      }
      return true;
    });
    list = [...list].sort((a, b) => {
      const ta = new Date(a.createdAt).getTime() || 0;
      const tb = new Date(b.createdAt).getTime() || 0;
      return sort === "oldest" ? ta - tb : tb - ta;
    });
    return list;
  }, [rows, search, bucketFilter, kindFilter, gradeFilter, sort, details]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pageRows = filtered.slice(
    (safePage - 1) * PAGE_SIZE,
    safePage * PAGE_SIZE,
  );
  const needReplyCount = rows.filter((r) => r.bucket === "needs_reply").length;

  return (
    <div className="space-y-4 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Triage</h1>
          <p className="text-xs mt-1" style={{ color: "var(--text-dim)" }}>
            Needs-first-reply first, stale second. Expand a row to grade it and
            act.
            {ranAt ? ` Last run ${ranAt}.` : ""}
          </p>
        </div>
        <button
          type="button"
          onClick={run}
          disabled={loading}
          data-testid="triage-run"
          className="flex items-center gap-1.5 px-4 py-2 rounded text-xs font-bold transition-colors disabled:opacity-50"
          style={{ background: "var(--amber)", color: "#000" }}
        >
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
          {loading ? "Scanning..." : "Run triage"}
        </button>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <textarea
          className="mono text-xs px-3 py-2 rounded outline-none w-full"
          rows={2}
          data-testid="triage-fleet"
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            color: "var(--text)",
          }}
          value={fleetText}
          onChange={(e) => setFleetText(e.target.value)}
          placeholder={"sandraschi/inkscape-mcp"}
        />
        <label className="text-xs" style={{ color: "var(--text-dim)" }}>
          Stale after
          <input
            type="number"
            min={1}
            max={90}
            value={staleDays}
            onChange={(e) => setStaleDays(Number(e.target.value) || 7)}
            className="mono text-xs px-2 py-1 rounded outline-none w-14 ml-1"
            style={{
              background: "var(--bg-2)",
              border: "1px solid var(--border)",
              color: "var(--text)",
            }}
          />
          days
        </label>
        {needReplyCount > 0 && (
          <span
            className="mono text-xs px-2 py-1 rounded"
            style={{
              background: "var(--red)",
              color: "#fff",
            }}
          >
            {needReplyCount} need first reply
          </span>
        )}
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <input
          className="mono text-xs px-3 py-1.5 rounded outline-none flex-1 min-w-40"
          data-testid="triage-search"
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            color: "var(--text)",
          }}
          value={search}
          onChange={(e) => setSearchPage(e.target.value)}
          placeholder="Search title, repo, author..."
        />
        {(
          [
            [
              "bucket",
              bucketFilter,
              setBucketPage,
              ["all", "needs_reply", "stale"],
            ],
            ["kind", kindFilter, setKindPage, ["all", "issue", "pr"]],
            ["sort", sort, setSortPage, ["oldest", "newest"]],
          ] as const
        ).map(([name, value, setValue, options]) => (
          <select
            key={name}
            value={value}
            data-testid={`triage-filter-${name}`}
            onChange={(e) => (setValue as (v: string) => void)(e.target.value)}
            className="mono text-xs px-2 py-1.5 rounded outline-none"
            style={{
              background: "var(--bg-2)",
              border: "1px solid var(--border)",
              color: "var(--text)",
            }}
          >
            {options.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        ))}
        <select
          value={gradeFilter}
          data-testid="triage-filter-grade"
          onChange={(e) => setGradePage(e.target.value as typeof gradeFilter)}
          className="mono text-xs px-2 py-1.5 rounded outline-none"
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            color: "var(--text)",
          }}
        >
          {(["all", "A", "B", "C", "D", "ungraded"] as const).map((o) => (
            <option key={o} value={o}>
              {o === "all"
                ? "all grades"
                : o === "ungraded"
                  ? "ungraded"
                  : `grade ${o}`}
            </option>
          ))}
        </select>
        <span
          className="mono text-xs ml-auto"
          style={{ color: "var(--text-dim)" }}
        >
          {filtered.length} of {rows.length}
        </span>
      </div>

      {error && (
        <div
          className="p-4 rounded text-sm mono"
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--red)",
            color: "var(--amber)",
          }}
        >
          {error} — ensure backend on :10713 and gh auth login.
        </div>
      )}

      {!loading && rows.length === 0 && !error && (
        <div
          className="p-8 text-center text-sm rounded"
          style={{
            color: "var(--text-dim)",
            border: "1px dashed var(--border)",
          }}
        >
          No results yet. Press Run triage.
        </div>
      )}

      <div
        data-testid="triage-list"
        className="rounded overflow-hidden"
        style={{ border: "1px solid var(--border)" }}
      >
        {pageRows.map((row, i) => {
          const detail = details[row.key];
          const assessment = detail?.assessment;
          const g = assessment ? GRADE_STYLE[assessment.grade] : null;
          return (
            <div
              key={row.key}
              className="px-4 py-3"
              style={{
                borderBottom:
                  i < pageRows.length - 1 ? "1px solid var(--border)" : "none",
              }}
            >
              <button
                type="button"
                onClick={() => toggleDetail(row)}
                className="w-full text-left flex items-start gap-3"
              >
                <AlertOctagon
                  size={14}
                  className="mt-0.5 shrink-0"
                  style={{
                    color:
                      row.bucket === "needs_reply"
                        ? "var(--red)"
                        : "var(--amber)",
                  }}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className="mono text-xs"
                      style={{ color: "var(--text-dim)" }}
                    >
                      {row.slug} #{row.number} · {row.kind}
                    </span>
                    <span
                      className="mono text-xs px-1.5 py-0.5 rounded"
                      style={{
                        border: "1px solid var(--border-2)",
                        color: "var(--text-muted)",
                      }}
                    >
                      {row.reason}
                    </span>
                    {assessment && g && (
                      <span
                        className="mono text-xs px-1.5 py-0.5 rounded font-bold"
                        style={{
                          border: `1px solid ${g.border}`,
                          color: g.color,
                        }}
                      >
                        {assessment.grade} · {assessment.gradeLabel}
                      </span>
                    )}
                    {acted[row.key] && (
                      <span
                        className="mono text-xs px-1.5 py-0.5 rounded"
                        style={{ background: "var(--green)", color: "#000" }}
                      >
                        {acted[row.key]}
                      </span>
                    )}
                  </div>
                  <div
                    className="text-sm font-medium truncate mt-0.5"
                    style={{ color: "var(--text)" }}
                  >
                    {row.title}
                  </div>
                  <div
                    className="text-xs mt-0.5"
                    style={{ color: "var(--text-dim)" }}
                  >
                    {row.author} · {relTime(row.createdAt)}
                    {row.commentCount >= 0 &&
                      ` · ${row.commentCount} comment${row.commentCount === 1 ? "" : "s"}`}
                  </div>
                </div>
              </button>

              {detail?.loading && (
                <div className="flex justify-center py-4">
                  <Loader2
                    size={16}
                    className="animate-spin"
                    style={{ color: "var(--amber)" }}
                  />
                </div>
              )}
              {detail?.error && (
                <div
                  className="text-xs mono mt-2"
                  style={{ color: "var(--red)" }}
                >
                  {detail.error}
                </div>
              )}
              {assessment && (
                <div
                  className="mt-3 rounded p-3 space-y-2"
                  style={{
                    background: "var(--bg-2)",
                    border: "1px solid var(--border)",
                  }}
                >
                  <div className="flex items-center gap-2 flex-wrap">
                    {assessment.signals.map((s) => (
                      <span
                        key={s}
                        className="mono text-xs px-1.5 py-0.5 rounded"
                        style={{
                          border: "1px solid var(--border-2)",
                          color: "var(--text-muted)",
                        }}
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                  <div className="text-xs">
                    <span
                      className="font-bold"
                      style={{ color: "var(--text)" }}
                    >
                      Plan:{" "}
                    </span>
                    <span style={{ color: "var(--text-muted)" }}>
                      {assessment.plan}
                    </span>
                  </div>
                  <textarea
                    className="w-full mono text-xs rounded p-2 outline-none"
                    rows={5}
                    style={{
                      background: "var(--bg-3)",
                      border: "1px solid var(--border)",
                      color: "var(--text)",
                    }}
                    value={replies[row.key] ?? ""}
                    onChange={(e) =>
                      setReplies((r) => ({ ...r, [row.key]: e.target.value }))
                    }
                  />
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => postReply(row)}
                      disabled={acting[row.key]}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-bold disabled:opacity-50"
                      style={{ background: "var(--green)", color: "#000" }}
                    >
                      <Send size={12} />{" "}
                      {acting[row.key] ? "Working..." : "Post reply"}
                    </button>
                    <button
                      type="button"
                      onClick={() => closeRow(row)}
                      disabled={acting[row.key]}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs disabled:opacity-50"
                      style={{
                        border: "1px solid var(--red)",
                        color: "var(--red)",
                      }}
                    >
                      <XCircle size={12} /> Close
                    </button>
                    <a
                      href={row.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs hover:underline ml-auto"
                      style={{ color: "var(--text-dim)" }}
                    >
                      Open in GitHub
                    </a>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center gap-2 justify-center">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={safePage <= 1}
            className="px-3 py-1 rounded text-xs disabled:opacity-40"
            style={{ border: "1px solid var(--border)", color: "var(--text)" }}
          >
            Prev
          </button>
          <span className="mono text-xs" style={{ color: "var(--text-dim)" }}>
            Page {safePage} of {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={safePage >= totalPages}
            className="px-3 py-1 rounded text-xs disabled:opacity-40"
            style={{ border: "1px solid var(--border)", color: "var(--text)" }}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
