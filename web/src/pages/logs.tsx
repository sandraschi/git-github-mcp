import { useCallback, useEffect, useState } from "react";
import { API_BASE } from "../lib/api";

type LogEntry = {
  id: string;
  timestamp: string;
  level: string;
  kind: string;
  detail: string;
};

export function LogsPage() {
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const params = new URLSearchParams({ limit: "100", sort: "desc" });
      if (search.trim()) params.set("search", search.trim());
      const r = await fetch(`${API_BASE}/api/logs?${params}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const j = await r.json();
      setEntries((j.entries as LogEntry[]) ?? []);
      setTotal(j.total ?? 0);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "load failed");
    }
  }, [search]);

  useEffect(() => {
    void load();
    const id = window.setInterval(() => void load(), 5000);
    return () => window.clearInterval(id);
  }, [load]);

  const clearLogs = async () => {
    await fetch(`${API_BASE}/api/logs`, { method: "DELETE" });
    void load();
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Fleet ring buffer at{" "}
        <code className="text-foreground/90">/api/logs</code> — {total} entries
      </p>
      <div className="flex flex-wrap gap-2">
        <input
          className="flex-1 min-w-[200px] rounded-md border border-border bg-background/80 px-3 py-2 text-sm"
          placeholder="Search logs…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button
          type="button"
          onClick={() => void load()}
          className="px-3 py-2 text-sm rounded border border-border"
        >
          Refresh
        </button>
        <button
          type="button"
          onClick={() => void clearLogs()}
          className="px-3 py-2 text-sm rounded border border-red-900/50 text-red-300"
        >
          Clear
        </button>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
      <div className="rounded-lg border border-border overflow-hidden font-mono text-xs">
        {entries.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No log entries yet.
          </div>
        ) : (
          entries.map((e) => (
            <div
              key={e.id}
              className="px-4 py-2 border-b border-border/60 last:border-0"
            >
              <span className="text-muted-foreground">{e.timestamp}</span>{" "}
              <span className="text-amber-400">{e.level}</span>{" "}
              <span className="text-gh-green">{e.kind}</span> — {e.detail}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
