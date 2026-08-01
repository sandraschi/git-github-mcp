import {
  Bot,
  Check,
  Compass,
  Copy,
  Download,
  Eraser,
  Loader2,
  Send,
  Terminal,
  User,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE, runDiscoveryWorkflow } from "@/lib/api";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
}

interface LlmProvider {
  id: string;
  name: string;
  base_url: string;
  models: string[];
  endpoint: string;
}

interface LlmDiscovery {
  success: boolean;
  any_available: boolean;
  providers: LlmProvider[];
  ollama_models: string[];
}

interface DiscoveryPresetMeta {
  id: string;
  title: string;
  blurb: string;
}

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const CHAT_STORAGE_KEY = "git-github-mcp-chat-history";
const CHAT_PERSONALITY_KEY = "git-github-mcp-chat-personality";
const CHAT_MODEL_KEY = "git-github-mcp-chat-model";
const CHAT_PROVIDER_KEY = "git-github-mcp-chat-provider";

const PERSONALITIES = [
  {
    id: "git-expert",
    label: "Git Expert",
    prompt:
      "You are a Git expert. Provide precise, production-safe git commands with clear explanations. Never suggest force-push to main. Always show the command first, then explain.",
  },
  {
    id: "gh-expert",
    label: "GitHub Expert",
    prompt:
      "You are a GitHub API and workflow expert. Use github_ops for all operations. Reference the correct gh CLI commands. Help with PRs, issues, Actions, releases, and repository management.",
  },
  {
    id: "reviewer",
    label: "Code Reviewer",
    prompt:
      "You are a thorough code reviewer. Evaluate diffs for correctness, style, security, and performance. Flag issues with severity (critical/major/minor/nit) and suggest fixes.",
  },
  {
    id: "release-mgr",
    label: "Release Manager",
    prompt:
      "You are a release manager. Help with semantic versioning, changelog generation, release notes, and deployment checklists. Know when to bump major vs minor vs patch.",
  },
  {
    id: "fleet-commander",
    label: "Fleet Commander",
    prompt:
      "You are a fleet operations commander. Use fleet_ops for registry audits, CI pulse checks, workspace scans, and full_suite runs. Know the port registry (10702 backend, 10703 frontend).",
  },
  {
    id: "custom",
    label: "Custom",
    prompt: "",
  },
];

const DISCOVERY_PRESETS: DiscoveryPresetMeta[] = [
  {
    id: "org_snapshot",
    title: "Org snapshot",
    blurb: "Verify gh auth, then list repos for an owner.",
  },
  {
    id: "topic_hunt",
    title: "Topic hunt",
    blurb: "Find repos by GitHub topic (tag); optional owner/text filter.",
  },
  {
    id: "code_sweep",
    title: "Code sweep",
    blurb: "Scoped code search; needs owner + query and/or file extension.",
  },
  {
    id: "repo_deep_dive",
    title: "Repo deep-dive",
    blurb: "Card, open issues, open PRs, then a Gitingest link.",
  },
  {
    id: "global_search",
    title: "Global search",
    blurb: "GitHub repo search with full query syntax.",
  },
];

const EXAMPLES = [
  "Show me the status of my repo",
  "List open PRs for sandraschi/git-github-mcp",
  "What are the recent commits?",
  "Create a release branch and bump version",
  "Find repos with stale .bak files",
  "Run a fleet workspace scan",
];

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function loadHistory(): Message[] {
  try {
    const saved = localStorage.getItem(CHAT_STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved) as Message[];
      return parsed.length > 100 ? parsed.slice(-100) : parsed;
    }
  } catch {
    /* ignore */
  }
  return [];
}

function saveHistory(msgs: Message[]) {
  try {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(msgs.slice(-100)));
  } catch {
    /* ignore */
  }
}

async function fetchSkillContent(): Promise<string> {
  try {
    const r = await fetch(`${API_BASE}/api/skill/github-expert`);
    if (r.ok) {
      const data = (await r.json()) as { content?: string };
      return data.content || "";
    }
  } catch {
    /* ignore */
  }
  return "";
}

async function fetchLlmDiscovery(): Promise<LlmDiscovery | null> {
  try {
    const r = await fetch(`${API_BASE}/api/llm/discover`);
    if (r.ok) return (await r.json()) as LlmDiscovery;
  } catch {
    /* ignore */
  }
  return null;
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export function Chat() {
  const [messages, setMessages] = useState<Message[]>(loadHistory);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [skillContent, setSkillContent] = useState("");
  const [llmDiscovery, setLlmDiscovery] = useState<LlmDiscovery | null>(null);

  const [personality, setPersonality] = useState(() => {
    try {
      return localStorage.getItem(CHAT_PERSONALITY_KEY) ?? "git-expert";
    } catch {
      return "git-expert";
    }
  });
  const [model, setModel] = useState(() => {
    try {
      return localStorage.getItem(CHAT_MODEL_KEY) ?? "";
    } catch {
      return "";
    }
  });
  const provider = (() => {
    try {
      return localStorage.getItem(CHAT_PROVIDER_KEY) ?? "ollama";
    } catch {
      return "ollama";
    }
  })();

  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Discovery panel state
  const [discPreset, setDiscPreset] = useState("org_snapshot");
  const [discOwner, setDiscOwner] = useState("");
  const [discRepo, setDiscRepo] = useState("");
  const [discQuery, setDiscQuery] = useState("");
  const [discTopic, setDiscTopic] = useState("");
  const [discExt, setDiscExt] = useState("");
  const [discLimit, setDiscLimit] = useState("25");
  const [discLoading, setDiscLoading] = useState(false);
  const [discResult, setDiscResult] = useState<string | null>(null);
  const [discCopied, setDiscCopied] = useState(false);
  const discOpen = false;

  /* -- init ------------------------------------------------------ */
  useEffect(() => {
    fetchSkillContent().then(setSkillContent);
    fetchLlmDiscovery().then((d) => {
      setLlmDiscovery(d);
      if (d && !model && d.ollama_models.length > 0) {
        setModel(d.ollama_models[0]);
      }
    });
  }, [model]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);
  useEffect(() => {
    localStorage.setItem(CHAT_PERSONALITY_KEY, personality);
  }, [personality]);
  useEffect(() => {
    localStorage.setItem(CHAT_MODEL_KEY, model);
  }, [model]);
  useEffect(() => {
    localStorage.setItem(CHAT_PROVIDER_KEY, provider);
  }, [provider]);
  useEffect(() => {
    saveHistory(messages);
  }, [messages]);

  /* -- LLM availability ------------------------------------------ */
  const ollamaAvailable = llmDiscovery?.any_available ?? false;
  const ollamaProvider = llmDiscovery?.providers?.find(
    (p) => p.id === "ollama",
  );
  const ollamaModels =
    ollamaProvider?.models ?? llmDiscovery?.ollama_models ?? [];
  const displayModel = model || ollamaModels[0] || "gemma3:12b";

  /* -- system prompt --------------------------------------------- */
  const personalityPrompt =
    PERSONALITIES.find((p) => p.id === personality)?.prompt ?? "";
  const systemPrompt =
    personality === "custom"
      ? personalityPrompt
      : `${skillContent || "## Git GitHub MCP Expert\n\nYou have 101+ operations across 11 tools."}\n\n---\n\n## Role\n${personalityPrompt}`;

  /* -- send ------------------------------------------------------ */
  const send = useCallback(
    async (text?: string) => {
      const msg = (text ?? input).trim();
      if (!msg || loading) return;
      const ts = () =>
        new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        });

      const userMsg: Message = { role: "user", content: msg, timestamp: ts() };
      setMessages((m) => [...m, userMsg]);
      setInput("");
      setLoading(true);

      // If no local LLM, use direct dispatch
      if (!ollamaAvailable) {
        try {
          const result = await dispatchCommand(msg);
          setMessages((m) => [
            ...m,
            { role: "assistant", content: result, timestamp: ts() },
          ]);
        } catch (e) {
          setMessages((m) => [
            ...m,
            { role: "assistant", content: `Error: ${e}`, timestamp: ts() },
          ]);
        } finally {
          setLoading(false);
        }
        return;
      }

      // Local LLM streaming
      const controller = new AbortController();
      abortRef.current = controller;
      const assistantMsg: Message = {
        role: "assistant",
        content: "",
        timestamp: ts(),
      };
      setMessages((m) => [...m, assistantMsg]);

      try {
        const chatMessages = [...messages.slice(-20), userMsg].map((m) => ({
          role: m.role as "user" | "assistant" | "system",
          content: m.content,
        }));

        const res = await fetch(`${API_BASE}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            messages: chatMessages,
            model: displayModel,
            provider,
            stream: true,
            system_prompt: systemPrompt,
          }),
          signal: controller.signal,
        });

        if (!res.ok) throw new Error(`LLM returned ${res.status}`);

        const reader = res.body?.getReader();
        if (!reader) throw new Error("No response body");
        const decoder = new TextDecoder();
        let buffer = "";
        let content = "";

        while (true) {
          const { done, value } = await reader.read();
          if (value) {
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() ?? "";
            for (const line of lines) {
              if (!line.trim()) continue;
              try {
                const ev = JSON.parse(line) as {
                  type: string;
                  content?: string;
                  error?: string;
                };
                if (ev.type === "token" && ev.content) {
                  content += ev.content;
                  setMessages((m) => {
                    const updated = [...m];
                    updated[updated.length - 1] = {
                      ...updated[updated.length - 1],
                      content,
                    };
                    return updated;
                  });
                } else if (ev.type === "error") {
                  content = `Error: ${ev.error}`;
                  setMessages((m) => {
                    const updated = [...m];
                    updated[updated.length - 1] = {
                      ...updated[updated.length - 1],
                      content,
                    };
                    return updated;
                  });
                }
              } catch {
                /* ignore parse errors */
              }
            }
          }
          if (done) {
            buffer += decoder.decode(undefined, { stream: false });
            if (buffer.trim()) {
              try {
                const ev = JSON.parse(buffer.trim()) as {
                  type: string;
                  content?: string;
                };
                if (ev.type === "token" && ev.content) {
                  content += ev.content;
                }
              } catch {
                /* ignore */
              }
            }
            setMessages((m) => {
              const updated = [...m];
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                content: content || "(no response)",
              };
              return updated;
            });
            break;
          }
        }
      } catch (e) {
        if ((e as Error).name === "AbortError") return;
        setMessages((m) => {
          const updated = [...m];
          const errMsg = `Error: ${e instanceof Error ? e.message : String(e)}`;
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: errMsg,
          };
          return updated;
        });
      } finally {
        setLoading(false);
        abortRef.current = null;
      }
    },
    [
      input,
      loading,
      ollamaAvailable,
      displayModel,
      provider,
      systemPrompt,
      messages,
    ],
  );

  /* -- actions --------------------------------------------------- */
  const clearChat = () => {
    setMessages([]);
    localStorage.removeItem(CHAT_STORAGE_KEY);
  };

  const exportChat = () => {
    const lines = messages.map(
      (m) => `[${m.timestamp}] ${m.role}: ${m.content}`,
    );
    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `git-github-mcp-chat-${new Date().toISOString().slice(0, 19).replace(/:/g, "-")}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  /* -- discovery ------------------------------------------------- */
  const runDiscovery = async () => {
    let lim = parseInt(discLimit, 10);
    if (Number.isNaN(lim)) lim = 25;
    setDiscLoading(true);
    setDiscCopied(false);
    setDiscResult(null);
    try {
      const raw = await runDiscoveryWorkflow({
        preset: discPreset,
        owner: discOwner.trim() || undefined,
        repo: discRepo.trim() || undefined,
        query: discQuery.trim() || undefined,
        topic: discTopic.trim() || undefined,
        extension: discExt.trim() || undefined,
        limit: lim,
      });
      setDiscResult(JSON.stringify(raw, null, 2));
    } catch (e) {
      setDiscResult(
        JSON.stringify({ success: false, error: String(e) }, null, 2),
      );
    } finally {
      setDiscLoading(false);
    }
  };

  const copyDiscovery = async () => {
    if (!discResult) return;
    try {
      await navigator.clipboard.writeText(discResult);
      setDiscCopied(true);
      setTimeout(() => setDiscCopied(false), 2000);
    } catch {
      /* ignore */
    }
  };

  const presetMeta = DISCOVERY_PRESETS.find((p) => p.id === discPreset);
  const hasMessages = messages.length > 0;

  /* -- render ---------------------------------------------------- */
  return (
    <div
      className="flex flex-col max-w-6xl"
      style={{ height: "calc(100vh - 5rem)" }}
      data-testid="chat-page"
    >
      {/* Controls bar */}
      <div
        className="flex items-center justify-between mb-3 gap-3"
        data-testid="chat-controls"
      >
        <div className="flex items-center gap-3 shrink-0">
          <h1 className="text-2xl font-bold">Chat</h1>
          {/* Provider status */}
          <div
            className="flex items-center gap-1.5 px-2 py-1 rounded text-xs"
            style={{
              background: "var(--bg-2)",
              border: "1px solid var(--border)",
            }}
          >
            {ollamaAvailable ? (
              <Wifi className="w-3 h-3" style={{ color: "var(--green)" }} />
            ) : (
              <WifiOff
                className="w-3 h-3"
                style={{ color: "var(--text-dim)" }}
              />
            )}
            <span
              className="font-mono"
              style={{
                color: ollamaAvailable ? "var(--green)" : "var(--text-dim)",
              }}
            >
              {ollamaAvailable ? `Ollama on :11434` : "No local LLM"}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          {/* Model input */}
          <input
            className="mono text-xs rounded px-2 py-1 outline-none w-36"
            style={{
              background: "var(--bg)",
              border: "1px solid var(--border)",
              color: "var(--cyan)",
            }}
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="gemma3:12b"
            disabled={!ollamaAvailable}
          />
          {/* Personality */}
          <select
            data-testid="personality-select"
            className="text-xs rounded px-2 py-1 bg-zinc-800 text-zinc-100 border border-zinc-600 outline-none"
            value={personality}
            onChange={(e) => setPersonality(e.target.value)}
          >
            {PERSONALITIES.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            data-testid="chat-export"
            onClick={exportChat}
            disabled={!hasMessages}
            className="p-1.5 rounded hover:bg-white/5 disabled:opacity-30"
            title="Export"
          >
            <Download className="h-4 w-4" />
          </button>
          <button
            type="button"
            data-testid="chat-clear"
            onClick={clearChat}
            disabled={!hasMessages}
            className="p-1.5 rounded hover:bg-white/5 disabled:opacity-30"
            title="Clear"
          >
            <Eraser className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-4 flex-1 min-h-0">
        {/* Message area */}
        <div className="flex flex-col flex-1 min-w-0 min-h-0">
          <div
            data-testid="chat-messages"
            className="flex-1 overflow-y-auto rounded space-y-1 p-3 mb-3"
            style={{
              background: "var(--bg-2)",
              border: "1px solid var(--border)",
            }}
          >
            {/* Greeting */}
            {messages.length === 0 && !loading && (
              <div className="flex flex-col items-center justify-center h-full text-center gap-3 p-6">
                <Terminal
                  size={32}
                  style={{ color: "var(--green)", opacity: 0.5 }}
                />
                <div>
                  <p
                    className="text-sm font-semibold"
                    style={{ color: "var(--text)" }}
                  >
                    {ollamaAvailable
                      ? `Local LLM ready (${displayModel})`
                      : "Command interface ready"}
                  </p>
                  <p
                    className="text-xs mt-1"
                    style={{ color: "var(--text-dim)" }}
                  >
                    {ollamaAvailable
                      ? "Ask questions about Git/GitHub workflows. Your chat is private and runs locally."
                      : "Type git or github commands, or pick an example below."}
                  </p>
                  {skillContent ? (
                    <p
                      className="text-xs mt-1 font-mono"
                      style={{ color: "var(--green)", opacity: 0.7 }}
                    >
                      skill:github-expert loaded
                    </p>
                  ) : null}
                </div>
              </div>
            )}
            {messages.map((m) => (
              <div
                key={`${m.role}-${m.timestamp}`}
                className={`flex gap-2 ${m.role === "user" ? "justify-end" : ""}`}
              >
                {m.role !== "user" && (
                  <div
                    className="h-6 w-6 rounded flex items-center justify-center shrink-0 mt-0.5"
                    style={{
                      background: "rgba(34,197,94,0.1)",
                      border: "1px solid var(--border)",
                    }}
                  >
                    <Bot size={11} style={{ color: "var(--green)" }} />
                  </div>
                )}
                <div
                  className={`max-w-[80%] flex flex-col gap-0.5 ${m.role === "user" ? "items-end" : "items-start"}`}
                >
                  <pre
                    className="mono text-xs rounded p-3 whitespace-pre-wrap break-all"
                    style={{
                      background:
                        m.role === "user" ? "var(--bg-3)" : "var(--bg)",
                      border: "1px solid var(--border)",
                      color: m.role === "user" ? "var(--cyan)" : "var(--text)",
                      maxHeight: 400,
                      overflowY: "auto",
                    }}
                  >
                    {m.content ||
                      (loading && m === messages[messages.length - 1] ? "▊" : "")}
                  </pre>
                  <span
                    className="text-xs"
                    style={{ color: "var(--text-dim)" }}
                  >
                    {m.timestamp}
                  </span>
                </div>
                {m.role === "user" && (
                  <div
                    className="h-6 w-6 rounded flex items-center justify-center shrink-0 mt-0.5"
                    style={{
                      background: "var(--bg-3)",
                      border: "1px solid var(--border)",
                    }}
                  >
                    <User size={11} style={{ color: "var(--text-muted)" }} />
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-2 px-2 py-1">
                <Loader2
                  size={12}
                  className="animate-spin"
                  style={{ color: "var(--green)" }}
                />
                <span
                  className="mono text-xs"
                  style={{ color: "var(--text-dim)" }}
                >
                  {ollamaAvailable ? "Thinking..." : "executing..."}
                </span>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Example prompts */}
          <div
            className="flex gap-1.5 flex-wrap mb-2"
            data-testid="example-prompts"
          >
            {EXAMPLES.map((ex) => (
              <button
                type="button"
                key={ex}
                onClick={() => send(ex)}
                className="mono text-xs px-2 py-1 rounded transition-colors hover:border-slate-600"
                style={{
                  background: "var(--bg-2)",
                  border: "1px solid var(--border)",
                  color: "var(--text-dim)",
                }}
              >
                {ex}
              </button>
            ))}
          </div>

          {/* Input */}
          <div
            className="flex items-center gap-2 px-3 py-2 rounded"
            style={{
              background: "var(--bg-2)",
              border: "1px solid var(--border-2)",
            }}
          >
            <span
              className="mono text-xs shrink-0"
              style={{ color: "var(--green)" }}
            >
              ❯
            </span>
            <input
              data-testid="chat-input"
              className="flex-1 bg-transparent mono text-sm outline-none"
              style={{ color: "var(--text)", caretColor: "var(--green)" }}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder={
                ollamaAvailable
                  ? "Ask about Git/GitHub..."
                  : "git status · github repos sandraschi"
              }
              disabled={loading}
            />
            <button
              type="button"
              data-testid="chat-send"
              onClick={() => send()}
              disabled={loading || !input.trim()}
              className="shrink-0 p-1 rounded transition-colors"
              style={{
                color: input.trim() ? "var(--green)" : "var(--text-dim)",
              }}
            >
              {loading ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Send size={14} />
              )}
            </button>
          </div>
        </div>

        {/* Discovery panel */}
        <aside
          className={`flex-col shrink-0 w-full lg:w-[22rem] rounded p-3 gap-3 overflow-y-auto ${
            discOpen ? "flex" : "hidden lg:flex"
          }`}
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            maxHeight: "min(70vh, 640px)",
          }}
        >
          <div className="flex items-start gap-2">
            <div
              className="h-8 w-8 rounded flex items-center justify-center shrink-0"
              style={{
                background: "var(--bg-3)",
                border: "1px solid var(--border)",
              }}
            >
              <Compass size={16} style={{ color: "var(--cyan)" }} />
            </div>
            <div>
              <h2
                className="text-sm font-semibold"
                style={{ color: "var(--text)" }}
              >
                Discovery workflow
              </h2>
              <p
                className="text-[11px] leading-snug mt-0.5"
                style={{ color: "var(--text-dim)" }}
              >
                Best: MCP{" "}
                <span className="mono">git_github_search_workflow</span>{" "}
                (LLM-planned). Here: fixed presets for web UI / without
                sampling.
              </p>
            </div>
          </div>
          <label className="flex flex-col gap-1 mt-2">
            <span
              className="text-[10px] uppercase tracking-wide"
              style={{ color: "var(--text-dim)" }}
            >
              Preset
            </span>
            <select
              className="mono text-xs rounded px-2 py-1.5 outline-none"
              style={{
                background: "var(--bg)",
                border: "1px solid var(--border)",
                color: "var(--text)",
              }}
              value={discPreset}
              onChange={(e) => setDiscPreset(e.target.value)}
              disabled={discLoading}
            >
              {DISCOVERY_PRESETS.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title}
                </option>
              ))}
            </select>
          </label>
          {presetMeta && (
            <p
              className="text-[11px] leading-snug -mt-1"
              style={{ color: "var(--text-muted)" }}
            >
              {presetMeta.blurb}
            </p>
          )}
          <div className="grid grid-cols-2 gap-2 mt-2">
            {(discPreset === "org_snapshot" ||
              discPreset === "topic_hunt" ||
              discPreset === "code_sweep" ||
              discPreset === "repo_deep_dive") && (
              <label className="flex flex-col gap-0.5 col-span-2">
                <span
                  className="text-[10px] mono"
                  style={{ color: "var(--text-dim)" }}
                >
                  owner
                </span>
                <input
                  className="mono text-xs rounded px-2 py-1 outline-none"
                  style={{
                    background: "var(--bg)",
                    border: "1px solid var(--border)",
                    color: "var(--cyan)",
                  }}
                  value={discOwner}
                  onChange={(e) => setDiscOwner(e.target.value)}
                  placeholder="user or org"
                  disabled={discLoading}
                />
              </label>
            )}
            {discPreset === "repo_deep_dive" && (
              <label className="flex flex-col gap-0.5 col-span-2">
                <span
                  className="text-[10px] mono"
                  style={{ color: "var(--text-dim)" }}
                >
                  repo
                </span>
                <input
                  className="mono text-xs rounded px-2 py-1 outline-none"
                  style={{
                    background: "var(--bg)",
                    border: "1px solid var(--border)",
                    color: "var(--cyan)",
                  }}
                  value={discRepo}
                  onChange={(e) => setDiscRepo(e.target.value)}
                  placeholder="name"
                  disabled={discLoading}
                />
              </label>
            )}
            {discPreset === "topic_hunt" && (
              <>
                <label className="flex flex-col gap-0.5 col-span-2">
                  <span
                    className="text-[10px] mono"
                    style={{ color: "var(--text-dim)" }}
                  >
                    topic
                  </span>
                  <input
                    className="mono text-xs rounded px-2 py-1 outline-none"
                    style={{
                      background: "var(--bg)",
                      border: "1px solid var(--border)",
                      color: "var(--cyan)",
                    }}
                    value={discTopic}
                    onChange={(e) => setDiscTopic(e.target.value)}
                    placeholder="e.g. mcp"
                    disabled={discLoading}
                  />
                </label>
                <label className="flex flex-col gap-0.5 col-span-2">
                  <span
                    className="text-[10px] mono"
                    style={{ color: "var(--text-dim)" }}
                  >
                    query (optional)
                  </span>
                  <input
                    className="mono text-xs rounded px-2 py-1 outline-none"
                    style={{
                      background: "var(--bg)",
                      border: "1px solid var(--border)",
                      color: "var(--cyan)",
                    }}
                    value={discQuery}
                    onChange={(e) => setDiscQuery(e.target.value)}
                    placeholder="extra search text"
                    disabled={discLoading}
                  />
                </label>
              </>
            )}
            {discPreset === "code_sweep" && (
              <>
                <label className="flex flex-col gap-0.5 col-span-2">
                  <span
                    className="text-[10px] mono"
                    style={{ color: "var(--text-dim)" }}
                  >
                    query
                  </span>
                  <input
                    className="mono text-xs rounded px-2 py-1 outline-none"
                    style={{
                      background: "var(--bg)",
                      border: "1px solid var(--border)",
                      color: "var(--cyan)",
                    }}
                    value={discQuery}
                    onChange={(e) => setDiscQuery(e.target.value)}
                    placeholder="code needle (optional)"
                    disabled={discLoading}
                  />
                </label>
                <label className="flex flex-col gap-0.5 col-span-2">
                  <span
                    className="text-[10px] mono"
                    style={{ color: "var(--text-dim)" }}
                  >
                    extension
                  </span>
                  <input
                    className="mono text-xs rounded px-2 py-1 outline-none"
                    style={{
                      background: "var(--bg)",
                      border: "1px solid var(--border)",
                      color: "var(--cyan)",
                    }}
                    value={discExt}
                    onChange={(e) => setDiscExt(e.target.value)}
                    placeholder="e.g. bak"
                    disabled={discLoading}
                  />
                </label>
              </>
            )}
            {discPreset === "global_search" && (
              <label className="flex flex-col gap-0.5 col-span-2">
                <span
                  className="text-[10px] mono"
                  style={{ color: "var(--text-dim)" }}
                >
                  query
                </span>
                <input
                  className="mono text-xs rounded px-2 py-1 outline-none"
                  style={{
                    background: "var(--bg)",
                    border: "1px solid var(--border)",
                    color: "var(--cyan)",
                  }}
                  value={discQuery}
                  onChange={(e) => setDiscQuery(e.target.value)}
                  placeholder="mcp language:python"
                  disabled={discLoading}
                />
              </label>
            )}
            <label className="flex flex-col gap-0.5 col-span-2">
              <span
                className="text-[10px] mono"
                style={{ color: "var(--text-dim)" }}
              >
                limit
              </span>
              <input
                type="number"
                min={1}
                max={100}
                className="mono text-xs rounded px-2 py-1 outline-none w-full"
                style={{
                  background: "var(--bg)",
                  border: "1px solid var(--border)",
                  color: "var(--text)",
                }}
                value={discLimit}
                onChange={(e) => setDiscLimit(e.target.value)}
                disabled={discLoading}
              />
            </label>
          </div>
          <button
            type="button"
            onClick={runDiscovery}
            disabled={discLoading}
            className="mono text-xs font-medium py-2 rounded transition-opacity mt-2"
            style={{
              background: "rgba(34,197,94,0.15)",
              border: "1px solid rgba(34,197,94,0.35)",
              color: "var(--green)",
              opacity: discLoading ? 0.6 : 1,
            }}
          >
            {discLoading ? (
              <span className="inline-flex items-center justify-center gap-2">
                <Loader2 size={14} className="animate-spin" /> Running...
              </span>
            ) : (
              "Run discovery workflow"
            )}
          </button>
          {discResult && (
            <div className="flex flex-col gap-1 flex-1 min-h-0 mt-2">
              <div className="flex items-center justify-between">
                <span
                  className="text-[10px] uppercase tracking-wide"
                  style={{ color: "var(--text-dim)" }}
                >
                  Result
                </span>
                <button
                  type="button"
                  onClick={copyDiscovery}
                  className="flex items-center gap-1 mono text-[10px] px-1.5 py-0.5 rounded"
                  style={{
                    border: "1px solid var(--border)",
                    color: "var(--text-muted)",
                  }}
                >
                  {discCopied ? (
                    <Check size={12} style={{ color: "var(--green)" }} />
                  ) : (
                    <Copy size={12} />
                  )}
                  {discCopied ? "Copied" : "Copy JSON"}
                </button>
              </div>
              <pre
                className="mono text-[10px] leading-relaxed rounded p-2 flex-1 overflow-auto whitespace-pre-wrap break-all"
                style={{
                  background: "var(--bg)",
                  border: "1px solid var(--border)",
                  color: "var(--text)",
                  maxHeight: 220,
                }}
              >
                {discResult}
              </pre>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Direct command dispatch (fallback when no local LLM)               */
/* ------------------------------------------------------------------ */

async function dispatchCommand(input: string): Promise<string> {
  // Dynamic imports for tree-shaking in LLM mode
  const { gitOps, githubOps } = await import("@/lib/api");

  const parts = input.trim().split(/\s+/);
  const cmd = parts[0]?.toLowerCase();

  if (cmd === "git" || cmd === "g") {
    const op = parts[1]?.toLowerCase();
    const repoPath =
      parts.find((p) => p.includes("/") || p.includes("\\")) ?? undefined;
    switch (op) {
      case "status":
        return JSON.stringify(
          await gitOps("status", { repo_path: repoPath }),
          null,
          2,
        );
      case "log": {
        const count = parseInt(
          parts.find((p) => p.startsWith("--count=") || /^\d+$/.test(p)) ??
            "10",
          10,
        );
        return JSON.stringify(
          await gitOps("log", {
            repo_path: repoPath,
            max_count: Number.isNaN(count) ? 10 : count,
          }),
          null,
          2,
        );
      }
      case "branches":
        return JSON.stringify(
          await gitOps("branch_list", { repo_path: repoPath }),
          null,
          2,
        );
      case "diff":
        return JSON.stringify(
          await gitOps("diff", { repo_path: repoPath }),
          null,
          2,
        );
      case "stash":
        return JSON.stringify(
          await gitOps("stash_list", { repo_path: repoPath }),
          null,
          2,
        );
      case "tags":
        return JSON.stringify(
          await gitOps("tag_list", { repo_path: repoPath }),
          null,
          2,
        );
      default:
        return `Unknown git sub-command: ${op}\nTry: status, log, branches, diff, stash, tags`;
    }
  }

  if (cmd === "github" || cmd === "gh") {
    const op = parts[1]?.toLowerCase();
    const owner = parts[2];
    const repo = parts[3];
    switch (op) {
      case "repos":
        return JSON.stringify(
          await githubOps("repo_list", { owner, limit: 20 }),
          null,
          2,
        );
      case "issues":
        return JSON.stringify(
          await githubOps("issue_list", { owner, repo, limit: 20 }),
          null,
          2,
        );
      case "prs":
        return JSON.stringify(
          await githubOps("pr_list", { owner, repo, limit: 20 }),
          null,
          2,
        );
      case "releases":
        return JSON.stringify(
          await githubOps("release_list", { owner, repo }),
          null,
          2,
        );
      case "find-bak":
        return JSON.stringify(
          await githubOps("code_find_repos", {
            owner,
            extension: "bak",
            limit: 50,
          }),
          null,
          2,
        );
      case "show":
        return JSON.stringify(
          await githubOps("show_repo", {
            owner,
            repo,
            output_format: "markdown",
          }),
          null,
          2,
        );
      case "gitingest":
        return JSON.stringify(
          await githubOps("gitingest_link", { owner, repo }),
          null,
          2,
        );
      case "gitingest-help":
        return JSON.stringify(await githubOps("gitingest_help"), null, 2);
      case "gitingest-url":
        return JSON.stringify(
          await githubOps("gitingest_convert_url", {
            github_url: parts.slice(2).join(" "),
          }),
          null,
          2,
        );
      case "search":
        return JSON.stringify(
          await githubOps("search_repos", { query: parts.slice(2).join(" ") }),
          null,
          2,
        );
      case "auth":
        return JSON.stringify(await githubOps("auth_status"), null, 2);
      default:
        return `Unknown github sub-command: ${op}\nTry: repos, issues, prs, releases, find-bak, show, gitingest, gitingest-help, gitingest-url, search, auth`;
    }
  }

  return `Unknown command: ${cmd}\n\nAvailable:\n  git status [path]\n  git log [--count N] [path]\n  git branches [path]\n  git diff [path]\n  git stash [path]\n  git tags [path]\n  github repos [owner]\n  github issues <owner> <repo>\n  github prs <owner> <repo>\n  github releases <owner> <repo>\n  github find-bak <owner>\n  github show <owner> <repo>\n  github gitingest <owner> <repo>\n  github gitingest-help\n  github gitingest-url <https://github.com/...>\n  github search <query>\n  github auth`;
}
