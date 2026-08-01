import { CircleDot, Loader2, Plus, RefreshCw, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { githubOps } from "@/lib/api";

interface Issue {
  number: number;
  title: string;
  state: string;
  url: string;
  author: { login: string };
  labels: { name: string; color: string }[];
  createdAt: string;
  updatedAt?: string;
}

export function Issues() {
  const [owner, setOwner] = useState("sandraschi");
  const [repo, setRepo] = useState("git-github-mcp");
  const [state, setState] = useState<"open" | "closed">("open");
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newBody, setNewBody] = useState("");

  const fetch = useCallback(() => {
    setLoading(true);
    setError(null);
    (
      githubOps("issue_list", { owner, repo, state, limit: 30 }) as Promise<{
        success: boolean;
        result?: { issues: Issue[] };
        error?: string;
      }>
    )
      .then((d) => {
        if (d.success) setIssues(d.result?.issues ?? []);
        else setError(d.error ?? "Failed");
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [owner, repo, state]);

  useEffect(fetch, [fetch]);

  const createIssue = async () => {
    if (!newTitle.trim()) return;
    setCreating(false);
    await githubOps("issue_create", {
      owner,
      repo,
      title: newTitle,
      body: newBody,
    });
    setNewTitle("");
    setNewBody("");
    fetch();
  };

  return (
    <div className="space-y-4 max-w-4xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Issues</h1>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setCreating((c) => !c)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors"
            style={{
              background: creating ? "var(--bg-3)" : "var(--green)",
              color: creating ? "var(--text-muted)" : "#000",
              border: "1px solid var(--green-dim)",
            }}
          >
            {creating ? <X size={12} /> : <Plus size={12} />}{" "}
            {creating ? "Cancel" : "New Issue"}
          </button>
          <button
            type="button"
            onClick={fetch}
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

      {/* Repo selector */}
      <div className="flex items-center gap-2">
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
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="Issue title..."
          />
          <textarea
            className="w-full bg-transparent outline-none text-xs mono resize-none"
            rows={3}
            style={{ color: "var(--text-muted)" }}
            value={newBody}
            onChange={(e) => setNewBody(e.target.value)}
            placeholder="Description (optional)..."
          />
          <button
            type="button"
            onClick={createIssue}
            className="px-4 py-1.5 rounded text-xs font-bold"
            style={{ background: "var(--green)", color: "#000" }}
          >
            Submit Issue
          </button>
        </div>
      )}

      {/* Issue list */}
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
          {error} — ensure gh is authed
        </div>
      ) : (
        <div
          className="rounded overflow-hidden"
          style={{ border: "1px solid var(--border)" }}
        >
          {issues.length === 0 ? (
            <div
              className="p-8 text-center text-sm"
              style={{ color: "var(--text-dim)" }}
            >
              No {state} issues
            </div>
          ) : (
            issues.map((iss, i) => (
              <div
                key={iss.number}
                className="flex items-start gap-3 px-4 py-3 hover:bg-white/[0.02] transition-colors"
                style={{
                  borderBottom:
                    i < issues.length - 1 ? "1px solid var(--border)" : "none",
                }}
              >
                <CircleDot
                  size={14}
                  className="mt-0.5 shrink-0"
                  style={{
                    color:
                      iss.state === "open" ? "var(--green)" : "var(--purple)",
                  }}
                />
                <div className="flex-1 min-w-0">
                  <a
                    href={iss.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm font-medium hover:underline truncate block"
                    style={{ color: "var(--text)" }}
                  >
                    {iss.title}
                  </a>
                  <div className="flex items-center gap-2 mt-1 flex-wrap">
                    <span
                      className="mono text-xs"
                      style={{ color: "var(--text-dim)" }}
                    >
                      #{iss.number}
                    </span>
                    <span
                      className="text-xs"
                      style={{ color: "var(--text-dim)" }}
                    >
                      {iss.author?.login}
                    </span>
                    {iss.labels?.map((l) => (
                      <span
                        key={l.name}
                        className="mono text-xs px-1.5 py-0.5 rounded"
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
                <div
                  className="mono text-xs shrink-0 text-right"
                  style={{ color: "var(--text-dim)" }}
                >
                  <div>{new Date(iss.createdAt).toLocaleDateString()}</div>
                  {iss.updatedAt && (
                    <div
                      className="text-[10px] mt-0.5"
                      style={{ color: "var(--text-muted)" }}
                    >
                      upd {new Date(iss.updatedAt).toLocaleDateString()}
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
