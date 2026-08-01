import { useEffect, useState } from "react";
import { useLogger } from "@/context/logger-context";
import { useCapabilities } from "@/hooks/use-capabilities";
import { API_BASE } from "../lib/api";

type ToolRow = {
  name: string;
  description?: string;
  operations?: number | string[];
};

export function ToolsPage() {
  const { append } = useLogger();
  const { caps, reload } = useCapabilities();
  const [tools, setTools] = useState<ToolRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/tools`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((j) => {
        const rows = (j.tools as ToolRow[]) ?? [];
        setTools(rows);
        append("INFO", `Loaded ${rows.length} tools from /api/tools`);
      })
      .catch((e) => append("ERROR", String(e)))
      .finally(() => setLoading(false));
  }, [append]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          MCP tool inspector — runtime from /api/capabilities
        </p>
        <button
          type="button"
          onClick={() => reload()}
          className="text-xs px-3 py-1.5 rounded border border-border hover:bg-white/5"
        >
          Refresh capabilities
        </button>
      </div>

      {caps && (
        <div className="grid sm:grid-cols-3 gap-3">
          {[
            ["Portmanteau", caps.tool_surface?.portmanteau_count ?? 0],
            ["Atomic", caps.tool_surface?.atomic_count ?? 0],
            ["Sampling", caps.features?.agentic_workflows ? "yes" : "no"],
          ].map(([k, v]) => (
            <div
              key={String(k)}
              className="rounded-lg border border-border bg-card/40 px-4 py-3 text-center"
            >
              <div className="text-xl font-semibold text-gh-green">
                {String(v)}
              </div>
              <div className="text-xs text-muted-foreground">{k}</div>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading tools…</p>
      ) : (
        <div className="rounded-lg border border-border overflow-hidden">
          {tools.map((t) => (
            <div
              key={t.name}
              className="px-4 py-3 border-b border-border/80 last:border-0"
            >
              <div className="font-mono text-sm text-gh-green">{t.name}</div>
              <div className="text-sm text-muted-foreground mt-1">
                {t.description ?? "—"}
              </div>
              {Array.isArray(t.operations) && (
                <div className="text-xs font-mono text-muted-foreground/80 mt-2">
                  ops: {t.operations.join(", ")}
                </div>
              )}
              {typeof t.operations === "number" && (
                <div className="text-xs text-muted-foreground/80 mt-1">
                  {t.operations} operations
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
