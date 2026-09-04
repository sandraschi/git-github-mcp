import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Clock,
  ExternalLink,
  FileCode2,
  Loader2,
  MinusCircle,
  Play,
  RefreshCw,
  RotateCcw,
  Wrench,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { githubOps, runCiDiagnose } from "@/lib/api";

interface WorkflowRun {
  databaseId: string;
  name?: string;
  status: string;
  conclusion: string | null;
  headBranch?: string;
  createdAt?: string;
  url?: string;
}

interface FailedStep {
  job: string;
  step: string;
  conclusion: string;
  log_tail: string;
}

interface RunDetail {
  run?: WorkflowRun;
  failures?: FailedStep[];
  failure_count?: number;
}

const FLEET_REPOS = [
  "sandraschi/git-github-mcp",
  "sandraschi/opencode-cli-mcp",
  "sandraschi/demo-vid-mcp",
  "sandraschi/scraper-mcp",
  "sandraschi/arxiv-mcp",
  "sandraschi/calibre-mcp",
  "sandraschi/mcp-central-docs",
];

const CONCLUSION_STYLE: Record<string, string> = {
  success: "bg-green-900/40 text-green-400",
  failure: "bg-red-900/40 text-red-400",
  cancelled: "bg-zinc-800 text-zinc-400",
  timed_out: "bg-amber-900/40 text-amber-400",
  neutral: "bg-zinc-800 text-zinc-400",
  skipped: "bg-zinc-800 text-zinc-500",
};

function ConclusionIcon({ c }: { c: string | null }) {
  if (c === "success")
    return <CheckCircle2 className="w-4 h-4 text-green-400" />;
  if (c === "failure") return <XCircle className="w-4 h-4 text-red-400" />;
  if (c === "cancelled" || c === "skipped" || c === "neutral")
    return <MinusCircle className="w-4 h-4 text-zinc-500" />;
  if (c === "timed_out") return <Clock className="w-4 h-4 text-amber-400" />;
  return <Activity className="w-4 h-4 text-blue-400 animate-pulse" />;
}

export function CiPage() {
  const [repo, setRepo] = useState("sandraschi/git-github-mcp");
  const [customRepo, setCustomRepo] = useState("");
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [diagnosis, setDiagnosis] = useState<string>("");
  const [diagnosing, setDiagnosing] = useState(false);
  const [error, setError] = useState("");
  const [triggered, setTriggered] = useState(false);
  const [showFailedOnly, setShowFailedOnly] = useState(false);

  const activeRepo = customRepo.trim() || repo;

  const loadRuns = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const d = (await githubOps("workflow_runs", {
        owner: activeRepo.split("/")[0],
        repo: activeRepo.split("/")[1],
        limit: 20,
      })) as { result: { runs: WorkflowRun[] } };
      setRuns(d?.result?.runs ?? []);
    } catch (e) {
      setError(
        `Failed to load runs: ${e instanceof Error ? e.message : "unknown"}`,
      );
    } finally {
      setLoading(false);
    }
  }, [activeRepo]);

  useEffect(() => {
    loadRuns();
  }, [loadRuns]);

  // Poll every 15s while a run is in progress.
  useEffect(() => {
    const hasRunning = runs.some(
      (r) => r.status === "in_progress" || r.status === "queued",
    );
    if (!hasRunning) return;
    const t = setInterval(loadRuns, 15000);
    return () => clearInterval(t);
  }, [runs, loadRuns]);

  const openRun = async (runId: string) => {
    setSelectedRun(runId);
    setDetailLoading(true);
    setDiagnosis("");
    try {
      const d = (await githubOps("workflow_view", {
        owner: activeRepo.split("/")[0],
        repo: activeRepo.split("/")[1],
        run_id: runId,
      })) as { result: RunDetail };
      setDetail(d?.result ?? {});
    } catch (e) {
      setError(
        `Failed to load run detail: ${e instanceof Error ? e.message : "unknown"}`,
      );
    } finally {
      setDetailLoading(false);
    }
  };

  const rerun = async (runId: string) => {
    if (!window.confirm(`Rerun workflow run ${runId}?`)) return;
    setError("");
    try {
      await githubOps("workflow_rerun", {
        owner: activeRepo.split("/")[0],
        repo: activeRepo.split("/")[1],
        run_id: runId,
      });
      setTriggered(true);
      setTimeout(() => setTriggered(false), 3000);
      setTimeout(loadRuns, 5000);
    } catch (e) {
      setError(`Rerun failed: ${e instanceof Error ? e.message : "unknown"}`);
    }
  };

  const triggerWorkflow = async () => {
    setError("");
    try {
      await githubOps("workflow_run", {
        owner: activeRepo.split("/")[0],
        repo: activeRepo.split("/")[1],
        workflow_id: "ci.yml",
      });
      setTriggered(true);
      setTimeout(() => setTriggered(false), 3000);
      setTimeout(loadRuns, 5000);
    } catch (e) {
      setError(`Trigger failed: ${e instanceof Error ? e.message : "unknown"}`);
    }
  };

  const diagnose = async () => {
    const failed = detail?.failures ?? [];
    if (failed.length === 0) {
      setDiagnosis("No failed steps found for this run.");
      return;
    }
    setDiagnosing(true);
    setError("");
    try {
      const logText = failed
        .map((f) => `[${f.job} / ${f.step}]\n${f.log_tail}`)
        .join("\n\n");
      const d = (await runCiDiagnose(logText, {
        repo: activeRepo,
        run_id: selectedRun,
      })) as {
        success: boolean;
        content: string;
      };
      setDiagnosis(d.content || "Diagnosis empty.");
    } catch (e) {
      setError(
        `Diagnose failed (LLM offline?): ${e instanceof Error ? e.message : "unknown"}`,
      );
    } finally {
      setDiagnosing(false);
    }
  };

  const inputCls =
    "bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent/50 font-mono";

  return (
    <div className="space-y-5 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="w-6 h-6 text-accent" />
            CI Monitor
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            Trigger, watch, and diagnose GitHub Actions runs — local or remote.
          </p>
        </div>
      </div>

      <div className="bg-surface-light border border-surface-border rounded-xl p-4 flex flex-wrap gap-2 items-end">
        <div>
          <label htmlFor="ci-repo" className="text-xs text-zinc-500 block mb-1">
            Repository
          </label>
          <select
            id="ci-repo"
            value={repo}
            onChange={(e) => {
              setRepo(e.target.value);
              setCustomRepo("");
            }}
            className={inputCls}
            data-testid="ci-repo-select"
          >
            {FLEET_REPOS.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label
            htmlFor="ci-custom-repo"
            className="text-xs text-zinc-500 block mb-1"
          >
            or custom owner/repo
          </label>
          <input
            id="ci-custom-repo"
            type="text"
            value={customRepo}
            onChange={(e) => setCustomRepo(e.target.value)}
            placeholder="owner/repo"
            className={`${inputCls} w-52`}
            data-testid="ci-custom-repo"
          />
        </div>
        <button
          type="button"
          onClick={loadRuns}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm bg-accent hover:bg-accent-hover text-white transition-colors"
          data-testid="ci-refresh"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
        <button
          type="button"
          onClick={triggerWorkflow}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm bg-zinc-800 text-zinc-300 hover:text-white transition-colors"
          data-testid="ci-trigger"
        >
          <Play className="w-4 h-4" />
          Trigger ci.yml
        </button>
        {triggered && (
          <span className="text-xs text-green-400">
            Triggered — refreshing…
          </span>
        )}
      </div>

      {/* Stats — success + failed together */}
      {runs.length > 0 && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {[
              { label: "Success", value: runs.filter((r) => r.conclusion === "success").length, color: "text-green-400", bg: "bg-green-900/20 border-green-800" },
              { label: "Failed", value: runs.filter((r) => r.conclusion === "failure").length, color: "text-red-400", bg: "bg-red-900/20 border-red-800" },
              { label: "Cancelled", value: runs.filter((r) => r.conclusion === "cancelled").length, color: "text-zinc-400", bg: "bg-zinc-800 border-zinc-700" },
              { label: "In progress", value: runs.filter((r) => r.status === "in_progress" || r.status === "queued").length, color: "text-blue-400", bg: "bg-blue-900/20 border-blue-800" },
              { label: "Total", value: runs.length, color: "text-zinc-200", bg: "bg-surface-light border-surface-border" },
            ].map((s) => (
              <div key={s.label} className={`rounded-lg border p-3 text-center ${s.bg}`}>
                <div className={`text-xl font-bold ${s.color}`}>{s.value}</div>
                <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{s.label}</div>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-3 text-xs">
            <span className="font-mono">
              Success rate: {runs.length ? Math.round((runs.filter((r) => r.conclusion === "success").length / runs.length) * 100) : 0}% ({runs.filter((r) => r.conclusion === "success").length}/{runs.length})
            </span>
            <span className="text-muted-foreground">·</span>
            <span className="text-muted-foreground">Last 20 runs — how to fix: red → open run → log tail → `just ci` locally → push → `Trigger ci.yml` / `Rerun failed` here. GH emails stop when bar goes green.</span>
          </div>
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-900/30 border border-red-800 rounded-lg text-sm text-red-400">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Runs list */}
        <section className="bg-surface-light border border-surface-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">
              Recent runs — {activeRepo}
            </h2>
            <label className="flex items-center gap-1.5 text-xs text-zinc-400 cursor-pointer">
              <input
                type="checkbox"
                checked={showFailedOnly}
                onChange={(e) => setShowFailedOnly(e.target.checked)}
                className="accent-red-500"
                data-testid="ci-filter-failed"
              />
              Failed only
            </label>
          </div>
          {loading && runs.length === 0 ? (
            <div className="flex justify-center py-8 text-zinc-500">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
          ) : runs.length === 0 ? (
            <p className="text-sm text-zinc-600">No runs found.</p>
          ) : (
            <div className="space-y-2 max-h-[560px] overflow-auto pr-1">
              {(showFailedOnly ? runs.filter((r) => r.conclusion === "failure") : runs).map((r) => (
                <button
                  key={r.databaseId}
                  type="button"
                  onClick={() => openRun(r.databaseId)}
                  className={`w-full text-left flex items-center gap-3 p-3 rounded-lg border transition-colors ${
                    selectedRun === r.databaseId
                      ? "border-accent/60 bg-accent/5"
                      : "border-surface-border hover:border-accent/30"
                  }`}
                  data-testid={`ci-run-${r.databaseId}`}
                >
                  <ConclusionIcon c={r.conclusion} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-zinc-200 truncate">
                        {r.name || `Run ${r.databaseId}`}
                      </span>
                      <span
                        className={`text-[10px] uppercase rounded px-1.5 py-0.5 ${
                          r.conclusion
                            ? (CONCLUSION_STYLE[r.conclusion] ??
                              "bg-zinc-800 text-zinc-400")
                            : "bg-blue-900/40 text-blue-400"
                        }`}
                      >
                        {r.conclusion || r.status}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-500 mt-0.5">
                      {r.headBranch} ·{" "}
                      {r.createdAt
                        ? new Date(r.createdAt).toLocaleString()
                        : ""}
                    </p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-zinc-600" />
                </button>
              ))}
            </div>
          )}
        </section>

        {/* Run detail */}
        <section className="bg-surface-light border border-surface-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">
              Run detail {selectedRun ? `#${selectedRun.slice(0, 10)}` : ""}
            </h2>
            {selectedRun && detail?.run?.url && (
              <a
                href={detail.run.url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-xs text-accent hover:underline"
              >
                GitHub <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>

          {detailLoading ? (
            <div className="flex justify-center py-8 text-zinc-500">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
          ) : !selectedRun ? (
            <p className="text-sm text-zinc-600">
              Select a run to see jobs, failures, and logs.
            </p>
          ) : (
            <div className="space-y-4 max-h-[560px] overflow-auto pr-1">
              {detail?.run?.conclusion === "success" && (
                <div className="flex items-center gap-2 p-3 bg-green-900/30 border border-green-800 rounded-lg text-sm text-green-400">
                  <CheckCircle2 className="w-4 h-4" />
                  Run passed — nothing to fix.
                </div>
              )}

              {detail?.failures && detail.failures.length > 0 ? (
                <>
                  <div className="flex items-center gap-2 p-3 bg-red-900/20 border border-red-900/50 rounded-lg text-sm text-red-300">
                    <XCircle className="w-4 h-4 shrink-0" />
                    <span>
                      {detail.failure_count} failed step
                      {detail.failure_count === 1 ? "" : "s"} — what failed is
                      below.
                    </span>
                  </div>

                  {detail.failures.map((f) => (
                    <div
                      key={`${f.job}-${f.step}`}
                      className="border border-surface-border rounded-lg overflow-hidden"
                    >
                      <div className="flex items-center gap-2 px-3 py-2 bg-zinc-900/60 text-xs text-zinc-300">
                        <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
                        <span className="font-semibold">{f.job}</span>
                        <span className="text-zinc-500">/</span>
                        <span className="font-mono">{f.step}</span>
                        <span className="ml-auto text-zinc-500">
                          {f.conclusion}
                        </span>
                      </div>
                      <pre className="p-3 text-xs text-red-300/90 font-mono whitespace-pre-wrap break-all max-h-48 overflow-auto bg-zinc-950">
                        {f.log_tail || "(no log captured)"}
                      </pre>
                    </div>
                  ))}

                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={diagnose}
                      disabled={diagnosing}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm bg-accent hover:bg-accent-hover text-white transition-colors disabled:opacity-50"
                      data-testid="ci-diagnose"
                    >
                      {diagnosing ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Wrench className="w-4 h-4" />
                      )}
                      AI Diagnose
                    </button>
                    <button
                      type="button"
                      onClick={() => rerun(selectedRun)}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm bg-zinc-800 text-zinc-300 hover:text-white transition-colors"
                      data-testid="ci-rerun"
                    >
                      <RotateCcw className="w-4 h-4" />
                      Rerun failed
                    </button>
                  </div>

                  {diagnosis && (
                    <div className="border border-accent/30 rounded-lg overflow-hidden">
                      <div className="flex items-center gap-2 px-3 py-2 bg-accent/10 text-xs text-accent font-semibold">
                        <Wrench className="w-3.5 h-3.5" />
                        AI Diagnosis
                      </div>
                      <div
                        className="p-3 text-sm text-zinc-200 whitespace-pre-wrap"
                        data-testid="ci-diagnosis"
                      >
                        {diagnosis}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                detail?.run && (
                  <div className="flex items-center gap-2 p-3 bg-zinc-900/40 border border-surface-border rounded-lg text-sm text-zinc-400">
                    <FileCode2 className="w-4 h-4" />
                    No failing steps detected (run may still be in progress or
                    skipped).
                  </div>
                )
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
