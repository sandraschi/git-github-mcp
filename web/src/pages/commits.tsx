import { ChevronDown, ChevronUp, GitCommit, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { gitOps } from "@/lib/api";

interface Entry {
  hash: string;
  author: string;
  email: string;
  date: string;
  subject: string;
}
interface LogData {
  success: boolean;
  data?: { count: number; entries: Entry[] };
  error?: string;
}

export function Commits() {
  const [repoPath, setRepoPath] = useState("D:/Dev/repos/git-github-mcp");
  const [log, setLog] = useState<LogData | null>(null);
  const [count, setCount] = useState(30);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);

  const fetchLog = () => {
    setLoading(true);
    (
      gitOps("log", { repo_path: repoPath, max_count: count }) as Promise<{
        success: boolean;
        result?: LogData["data"];
      }>
    )
      .then((d) => setLog({ success: d?.success ?? false, data: d?.result }))
      .catch((e) => setLog({ success: false, error: String(e) }))
      .finally(() => setLoading(false));
  };

  useEffect(fetchLog, [repoPath, count]);

  const entries = log?.data?.entries ?? [];

  return (
    <div className="space-y-4 max-w-4xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Commit Log</h1>
        <select
          className="mono text-xs px-3 py-1.5 rounded outline-none"
          style={{
            background: "var(--bg-3)",
            border: "1px solid var(--border)",
            color: "var(--text-muted)",
          }}
          value={count}
          onChange={(e) => setCount(Number(e.target.value))}
        >
          {[10, 20, 30, 50, 100].map((n) => (
            <option key={n} value={n}>
              {n} commits
            </option>
          ))}
        </select>
      </div>

      {/* Repo input */}
      <div
        className="flex items-center gap-2 px-3 py-2 rounded"
        style={{ background: "var(--bg-2)", border: "1px solid var(--border)" }}
      >
        <span className="mono text-xs" style={{ color: "var(--text-dim)" }}>
          $
        </span>
        <input
          className="flex-1 bg-transparent mono text-xs outline-none"
          style={{ color: "var(--green)" }}
          value={repoPath}
          onChange={(e) => setRepoPath(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && fetchLog()}
          placeholder="repo path..."
        />
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2
            className="animate-spin"
            size={20}
            style={{ color: "var(--green)" }}
          />
        </div>
      ) : log?.success === false ? (
        <div
          className="rounded p-6 text-center mono text-sm"
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            color: "var(--red)",
          }}
        >
          {log.error || "Failed to load log"}
        </div>
      ) : (
        <div
          className="rounded overflow-hidden"
          style={{ border: "1px solid var(--border)" }}
        >
          {/* Timeline */}
          <div className="divide-y" style={{ borderColor: "var(--border)" }}>
            {entries.map((e, i) => (
              <div key={e.hash}>
                <button
                  type="button"
                  className="w-full text-left flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-white/[0.02] transition-colors"
                  onClick={() =>
                    setExpanded(expanded === e.hash ? null : e.hash)
                  }
                >
                  {/* Graph line */}
                  <div
                    className="flex flex-col items-center shrink-0"
                    style={{ width: 16 }}
                  >
                    <div
                      className="h-2 w-2 rounded-full"
                      style={{
                        background:
                          i === 0 ? "var(--green)" : "var(--border-2)",
                      }}
                    />
                    {i < entries.length - 1 && (
                      <div
                        className="flex-1 w-px mt-1"
                        style={{ background: "var(--border)", minHeight: 8 }}
                      />
                    )}
                  </div>
                  <span className="hash-chip shrink-0">
                    {e.hash.slice(0, 7)}
                  </span>
                  <span className="flex-1 text-sm truncate">{e.subject}</span>
                  <span
                    className="text-xs shrink-0 mono"
                    style={{ color: "var(--text-dim)" }}
                  >
                    {e.date}
                  </span>
                  {expanded === e.hash ? (
                    <ChevronUp size={12} style={{ color: "var(--text-dim)" }} />
                  ) : (
                    <ChevronDown
                      size={12}
                      style={{ color: "var(--text-dim)" }}
                    />
                  )}
                </button>
                {expanded === e.hash && (
                  <div
                    className="px-10 py-3 mono text-xs space-y-1"
                    style={{
                      background: "var(--bg-3)",
                      borderTop: "1px solid var(--border)",
                    }}
                  >
                    <div>
                      <span style={{ color: "var(--text-dim)" }}>hash: </span>
                      <span style={{ color: "var(--green)" }}>{e.hash}</span>
                    </div>
                    <div>
                      <span style={{ color: "var(--text-dim)" }}>author: </span>
                      <span style={{ color: "var(--text)" }}>
                        {e.author} &lt;{e.email}&gt;
                      </span>
                    </div>
                    <div>
                      <span style={{ color: "var(--text-dim)" }}>date: </span>
                      <span style={{ color: "var(--cyan)" }}>{e.date}</span>
                    </div>
                    <div>
                      <span style={{ color: "var(--text-dim)" }}>msg: </span>
                      <span style={{ color: "var(--text)" }}>{e.subject}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {entries.length > 0 && (
        <p
          className="text-xs mono text-right"
          style={{ color: "var(--text-dim)" }}
        >
          {entries.length} commits shown ·{" "}
          <GitCommit size={10} className="inline" />
        </p>
      )}
    </div>
  );
}
