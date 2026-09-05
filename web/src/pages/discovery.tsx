import { Check, Compass, Copy, Github, Loader2, Search } from "lucide-react";
import { useState } from "react";
import { runDiscoveryWorkflow } from "@/lib/api";

const PRESETS = [
  {
    id: "org_snapshot",
    title: "Org snapshot",
    blurb: "Verify gh auth, then list repos for an owner.",
    inputs: ["owner (user/org)"],
    does: "Calls `gh auth status` to confirm auth, then `github_ops(repo_list)` for the owner. Returns repo count, private/public split and sample names.",
    example: `{ preset: "org_snapshot", owner: "sandraschi", limit: 25 }`,
    tool: "git_github_search_workflow(task='org snapshot for {owner}')",
  },
  {
    id: "topic_hunt",
    title: "Topic hunt",
    blurb: "Find repos by GitHub topic (tag); optional owner/text filter.",
    inputs: [
      "topic (required)",
      "owner (optional)",
      "query (optional text)",
      "limit",
    ],
    does: "Uses `search_repos_topic` / `search_repos` with topic filter. Good for `mcp`, `tauri`, `automation` across the fleet or a single owner.",
    example: `{ preset: "topic_hunt", topic: "mcp", owner: "sandraschi", limit: 25 }`,
    tool: "github_ops(search_repos_topic)",
  },
  {
    id: "code_sweep",
    title: "Code sweep",
    blurb: "Scoped code search; needs owner + query and/or file extension.",
    inputs: ["owner", "query (needle)", "extension (e.g. bak, ps1)", "limit"],
    does: "Calls `search_code` / `code_find_repos`. Finds e.g. all repos with stale `.bak` files or fleet-wide `assfix` dross.",
    example: `{ preset: "code_sweep", owner: "sandraschi", query: "assfix", extension: "bak", limit: 50 }`,
    tool: "github_ops(code_find_repos, search_code)",
  },
  {
    id: "repo_deep_dive",
    title: "Repo deep-dive",
    blurb: "Card, open issues, open PRs, then a Gitingest link.",
    inputs: ["owner", "repo", "limit"],
    does: "Fetches `show_repo` card, `issue_list`, `pr_list`, then `gitingest_link` for a single repo. One-shot health + backlog + ingest.",
    example: `{ preset: "repo_deep_dive", owner: "sandraschi", repo: "git-github-mcp", limit: 10 }`,
    tool: "github_ops(show_repo, issue_list, pr_list, gitingest_link)",
  },
  {
    id: "global_search",
    title: "Global search",
    blurb: "GitHub repo search with full query syntax.",
    inputs: ["query (GitHub search syntax)", "limit"],
    does: "Direct `search_repos` with raw query like `mcp language:python stars:>10`. No owner scoping, global.",
    example: `{ preset: "global_search", query: "mcp language:python", limit: 25 }`,
    tool: "github_ops(search_repos)",
  },
] as const;

export function DiscoveryPage() {
  const [preset, setPreset] = useState<string>("org_snapshot");
  const [owner, setOwner] = useState("");
  const [repo, setRepo] = useState("");
  const [query, setQuery] = useState("");
  const [topic, setTopic] = useState("");
  const [ext, setExt] = useState("");
  const [limit, setLimit] = useState("25");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const meta = PRESETS.find((p) => p.id === preset) ?? PRESETS[0];

  const run = async () => {
    let lim = parseInt(limit, 10);
    if (Number.isNaN(lim)) lim = 25;
    setLoading(true);
    setResult(null);
    setCopied(false);
    try {
      const raw = await runDiscoveryWorkflow({
        preset,
        owner: owner.trim() || undefined,
        repo: repo.trim() || undefined,
        query: query.trim() || undefined,
        topic: topic.trim() || undefined,
        extension: ext.trim() || undefined,
        limit: lim,
      });
      setResult(JSON.stringify(raw, null, 2));
    } catch (e) {
      setResult(JSON.stringify({ success: false, error: String(e) }, null, 2));
    } finally {
      setLoading(false);
    }
  };

  const copy = async () => {
    if (!result) return;
    await navigator.clipboard.writeText(result);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-6xl" data-testid="discovery-page">
      <div className="rounded-2xl border border-border bg-card/40 p-6">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center">
            <Compass className="w-4 h-4 text-sky-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Discovery</h1>
            <p className="text-sm text-muted-foreground mt-1 max-w-[70ch]">
              Fixed presets for web UI without LLM sampling. For agentic runs
              use MCP{" "}
              <span className="font-mono text-xs bg-white/5 border border-white/10 px-1 py-0.5 rounded">
                git_github_search_workflow
              </span>{" "}
              — it LLM-plans the same presets.
            </p>
          </div>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {PRESETS.map((p) => (
          <button
            type="button"
            key={p.id}
            onClick={() => setPreset(p.id)}
            className={`text-left rounded-xl border p-4 transition-colors ${preset === p.id ? "bg-sky-500/10 border-sky-500/30" : "bg-card/40 border-border hover:border-white/10"}`}
            data-testid={`preset-${p.id}`}
          >
            <div className="font-semibold text-sm flex items-center gap-2">
              <Search className="w-3.5 h-3.5 text-muted-foreground" /> {p.title}
            </div>
            <p className="text-xs text-muted-foreground mt-1">{p.blurb}</p>
            <p className="text-[11px] font-mono text-muted-foreground/60 mt-2">
              inputs: {p.inputs.join(" · ")}
            </p>
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[22rem_1fr]">
        <div className="rounded-xl border border-border bg-card/40 p-4 space-y-3 h-fit">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <Compass className="w-4 h-4 text-sky-400" /> Run {meta.title}
          </h2>
          <p className="text-xs text-muted-foreground">{meta.does}</p>
          <p className="text-[11px] font-mono bg-black/30 border border-white/5 rounded p-2">
            {meta.example}
          </p>
          <p className="text-[11px] font-mono text-muted-foreground">
            tool: {meta.tool}
          </p>

          <div className="space-y-2 pt-2">
            <label className="flex flex-col gap-1">
              <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
                Preset
              </span>
              <select
                value={preset}
                onChange={(e) => setPreset(e.target.value)}
                className="mono text-xs rounded px-2 py-1.5 bg-background border border-border"
              >
                {PRESETS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.title}
                  </option>
                ))}
              </select>
            </label>
            {(preset === "org_snapshot" ||
              preset === "topic_hunt" ||
              preset === "code_sweep" ||
              preset === "repo_deep_dive") && (
              <label className="flex flex-col gap-1">
                <span className="text-[10px] mono text-muted-foreground">
                  owner
                </span>
                <input
                  value={owner}
                  onChange={(e) => setOwner(e.target.value)}
                  placeholder="user or org"
                  className="mono text-xs rounded px-2 py-1 bg-background border border-border"
                />
              </label>
            )}
            {preset === "repo_deep_dive" && (
              <label className="flex flex-col gap-1">
                <span className="text-[10px] mono text-muted-foreground">
                  repo
                </span>
                <input
                  value={repo}
                  onChange={(e) => setRepo(e.target.value)}
                  placeholder="name"
                  className="mono text-xs rounded px-2 py-1 bg-background border border-border"
                />
              </label>
            )}
            {preset === "topic_hunt" && (
              <>
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] mono text-muted-foreground">
                    topic
                  </span>
                  <input
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g. mcp"
                    className="mono text-xs rounded px-2 py-1 bg-background border border-border"
                  />
                </label>
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] mono text-muted-foreground">
                    query (optional)
                  </span>
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="extra text"
                    className="mono text-xs rounded px-2 py-1 bg-background border border-border"
                  />
                </label>
              </>
            )}
            {preset === "code_sweep" && (
              <>
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] mono text-muted-foreground">
                    query
                  </span>
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="code needle"
                    className="mono text-xs rounded px-2 py-1 bg-background border border-border"
                  />
                </label>
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] mono text-muted-foreground">
                    extension
                  </span>
                  <input
                    value={ext}
                    onChange={(e) => setExt(e.target.value)}
                    placeholder="e.g. bak"
                    className="mono text-xs rounded px-2 py-1 bg-background border border-border"
                  />
                </label>
              </>
            )}
            {preset === "global_search" && (
              <label className="flex flex-col gap-1">
                <span className="text-[10px] mono text-muted-foreground">
                  query
                </span>
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="mcp language:python"
                  className="mono text-xs rounded px-2 py-1 bg-background border border-border"
                />
              </label>
            )}
            <label className="flex flex-col gap-1">
              <span className="text-[10px] mono text-muted-foreground">
                limit
              </span>
              <input
                type="number"
                min={1}
                max={100}
                value={limit}
                onChange={(e) => setLimit(e.target.value)}
                className="mono text-xs rounded px-2 py-1 bg-background border border-border"
              />
            </label>
            <button
              type="button"
              onClick={run}
              disabled={loading}
              className="w-full mono text-xs font-medium py-2 rounded bg-sky-500/15 border border-sky-500/30 text-sky-400 hover:bg-sky-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Running…
                </>
              ) : (
                "Run discovery"
              )}
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card/40 p-4 min-h-[300px] flex flex-col">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">Result</h2>
            <button
              type="button"
              onClick={copy}
              disabled={!result}
              className="mono text-xs px-2 py-1 rounded border border-border disabled:opacity-40 flex items-center gap-1"
            >
              {copied ? (
                <Check className="w-3 h-3 text-green-500" />
              ) : (
                <Copy className="w-3 h-3" />
              )}{" "}
              {copied ? "Copied" : "Copy JSON"}
            </button>
          </div>
          <pre className="mono text-xs bg-black/30 border border-white/5 rounded p-3 mt-3 flex-1 overflow-auto whitespace-pre-wrap break-all max-h-[60vh]">
            {result ??
              "Run a preset to see JSON. Use the MCP tool for LLM-planned runs."}
          </pre>
          <p className="text-[11px] text-muted-foreground mt-2 flex items-center gap-1">
            <Github className="w-3 h-3" /> Best is still{" "}
            <span className="font-mono">git_github_search_workflow</span> via
            MCP.
          </p>
        </div>
      </div>

      <div className="rounded-xl border border-dashed border-border bg-black/10 p-4">
        <h3 className="text-sm font-semibold">
          All discovery items — what each does
        </h3>
        <div className="mt-3 grid gap-3">
          {PRESETS.map((p) => (
            <div
              key={p.id}
              className="rounded-lg border border-border bg-card/30 p-4"
            >
              <div className="font-mono text-xs text-sky-400">{p.id}</div>
              <div className="font-semibold text-sm">{p.title}</div>
              <p className="text-xs text-muted-foreground mt-1">{p.blurb}</p>
              <p className="text-xs mt-2">
                <span className="font-semibold">Inputs:</span>{" "}
                {p.inputs.join(" · ")}
              </p>
              <p className="text-xs mt-1">
                <span className="font-semibold">Does:</span> {p.does}
              </p>
              <p className="text-[11px] font-mono bg-black/20 border border-white/5 rounded px-2 py-1 mt-2">
                {p.tool}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
