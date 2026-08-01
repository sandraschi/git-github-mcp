import {
  Circle,
  GitPullRequest,
  Loader2,
  Plus,
  RefreshCw,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { githubOps } from "@/lib/api";

interface PR {
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
}

export function PullRequests() {
  const [owner, setOwner] = useState("sandraschi");
  const [repo, setRepo] = useState("git-github-mcp");
  const [state, setState] = useState<"open" | "closed">("open");
  const [prs, setPrs] = useState<PR[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    title: "",
    body: "",
    head: "",
    base: "main",
    draft: false,
  });

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    (
      githubOps("pr_list", { owner, repo, state, limit: 30 }) as Promise<{
        success: boolean;
        result?: { prs: PR[] };
        error?: string;
      }>
    )
      .then((d) => {
        if (d.success) setPrs(d.result?.prs ?? []);
        else setError(d.error ?? "Failed");
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [owner, repo, state]);

  useEffect(load, [load]);

  const createPR = async () => {
    if (!form.title.trim()) return;
    setCreating(false);
    await githubOps("pr_create", {
      owner,
      repo,
      title: form.title,
      body: form.body,
      head_branch: form.head,
      base_branch: form.base,
      draft: form.draft,
    });
    setForm({ title: "", body: "", head: "", base: "main", draft: false });
    load();
  };

  return (
    <div className="space-y-4 max-w-4xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Pull Requests</h1>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setCreating((c) => !c)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium"
            style={{
              background: creating ? "var(--bg-3)" : "var(--blue)",
              color: creating ? "var(--text-muted)" : "#fff",
              border: `1px solid ${creating ? "var(--border)" : "var(--blue-dim)"}`,
            }}
          >
            {creating ? <X size={12} /> : <Plus size={12} />}
            {creating ? "Cancel" : "New PR"}
          </button>
          <button
            type="button"
            onClick={load}
            className="p-1.5 rounded"
            style={{
              border: "1px solid var(--border)",
              color: "var(--text-muted)",
            }}
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* Repo + state selector */}
      <div className="flex items-center gap-2 flex-wrap">
        <input
          className="mono text-xs px-3 py-1.5 rounded outline-none w-36"
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            color: "var(--text)",
          }}
          value={owner}
          onChange={(e) => setOwner(e.target.value)}
          placeholder="owner"
        />
        <span style={{ color: "var(--text-dim)" }}>/</span>
        <input
          className="mono text-xs px-3 py-1.5 rounded outline-none flex-1"
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            color: "var(--text)",
          }}
          value={repo}
          onChange={(e) => setRepo(e.target.value)}
          placeholder="repo"
        />
        {(["open", "closed"] as const).map((s) => (
          <button
            type="button"
            key={s}
            onClick={() => setState(s)}
            className="px-3 py-1.5 rounded text-xs transition-colors"
            style={{
              background: state === s ? "var(--bg-3)" : "transparent",
              color: state === s ? "var(--text)" : "var(--text-dim)",
              border: `1px solid ${state === s ? "var(--border-2)" : "var(--border)"}`,
            }}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Create form */}
      {creating && (
        <div
          className="rounded p-4 space-y-3"
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--border-2)",
          }}
        >
          <input
            className="w-full bg-transparent outline-none text-sm"
            style={{
              borderBottom: "1px solid var(--border)",
              paddingBottom: 6,
              color: "var(--text)",
            }}
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
            placeholder="PR title..."
          />
          <div className="flex items-center gap-2">
            <input
              className="mono text-xs px-3 py-1.5 rounded outline-none flex-1"
              style={{
                background: "var(--bg-3)",
                border: "1px solid var(--border)",
                color: "var(--text)",
              }}
              value={form.head}
              onChange={(e) => setForm((f) => ({ ...f, head: e.target.value }))}
              placeholder="head branch"
            />
            <span style={{ color: "var(--text-dim)" }}>→</span>
            <input
              className="mono text-xs px-3 py-1.5 rounded outline-none w-28"
              style={{
                background: "var(--bg-3)",
                border: "1px solid var(--border)",
                color: "var(--text)",
              }}
              value={form.base}
              onChange={(e) => setForm((f) => ({ ...f, base: e.target.value }))}
              placeholder="base"
            />
            <label
              className="flex items-center gap-1.5 text-xs cursor-pointer"
              style={{ color: "var(--text-muted)" }}
            >
              <input
                type="checkbox"
                checked={form.draft}
                onChange={(e) =>
                  setForm((f) => ({ ...f, draft: e.target.checked }))
                }
              />
              Draft
            </label>
          </div>
          <textarea
            className="w-full bg-transparent outline-none text-xs mono resize-none"
            rows={3}
            style={{ color: "var(--text-muted)" }}
            value={form.body}
            onChange={(e) => setForm((f) => ({ ...f, body: e.target.value }))}
            placeholder="Description (optional)..."
          />
          <button
            type="button"
            onClick={createPR}
            className="px-4 py-1.5 rounded text-xs font-bold"
            style={{ background: "var(--blue)", color: "#fff" }}
          >
            Create Pull Request
          </button>
        </div>
      )}

      {/* PR list */}
      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2
            className="animate-spin"
            size={20}
            style={{ color: "var(--blue)" }}
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
          {error} — run <span className="text-white">gh auth login</span>
        </div>
      ) : (
        <div
          className="rounded overflow-hidden"
          style={{ border: "1px solid var(--border)" }}
        >
          {prs.length === 0 ? (
            <div
              className="p-8 text-center text-sm"
              style={{ color: "var(--text-dim)" }}
            >
              No {state} pull requests
            </div>
          ) : (
            prs.map((pr, i) => (
              <div
                key={pr.number}
                className="flex items-start gap-3 px-4 py-3 hover:bg-white/[0.02] transition-colors"
                style={{
                  borderBottom:
                    i < prs.length - 1 ? "1px solid var(--border)" : "none",
                }}
              >
                <GitPullRequest
                  size={14}
                  className="mt-0.5 shrink-0"
                  style={{
                    color: pr.isDraft
                      ? "var(--text-dim)"
                      : pr.state === "open"
                        ? "var(--green)"
                        : "var(--purple)",
                  }}
                />
                <div className="flex-1 min-w-0">
                  <a
                    href={pr.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm font-medium hover:underline truncate block"
                    style={{ color: "var(--text)" }}
                  >
                    {pr.title}
                    {pr.isDraft && (
                      <span
                        className="ml-2 mono text-xs px-1.5 py-0.5 rounded"
                        style={{
                          background: "var(--bg-3)",
                          color: "var(--text-dim)",
                          border: "1px solid var(--border)",
                        }}
                      >
                        Draft
                      </span>
                    )}
                  </a>
                  <div className="flex items-center gap-2 mt-1 flex-wrap">
                    <span
                      className="mono text-xs"
                      style={{ color: "var(--text-dim)" }}
                    >
                      #{pr.number}
                    </span>
                    <span
                      className="text-xs"
                      style={{ color: "var(--text-dim)" }}
                    >
                      {pr.author?.login}
                    </span>
                    {typeof pr.comments === "number" && (
                      <span
                        className="text-xs"
                        style={{ color: "var(--text-muted)" }}
                      >
                        {pr.comments} comments
                      </span>
                    )}
                    <span
                      className="mono text-xs flex items-center gap-1"
                      style={{ color: "var(--cyan)" }}
                    >
                      <Circle size={6} fill="currentColor" />
                      {pr.headRefName}
                    </span>
                    <span style={{ color: "var(--text-dim)" }}>→</span>
                    <span
                      className="mono text-xs"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {pr.baseRefName}
                    </span>
                  </div>
                </div>
                <div
                  className="mono text-xs shrink-0 text-right"
                  style={{ color: "var(--text-dim)" }}
                >
                  <div>{new Date(pr.createdAt).toLocaleDateString()}</div>
                  {pr.updatedAt && (
                    <div
                      className="text-[10px] mt-0.5"
                      style={{ color: "var(--text-muted)" }}
                    >
                      upd {new Date(pr.updatedAt).toLocaleDateString()}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
