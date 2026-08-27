/** Shared API client — dev uses Vite proxy (/api → :10713); prod uses VITE_API_URL or :10713 */

export const API_BASE = "http://127.0.0.1:10713";

const BASE =
  import.meta.env.VITE_API_URL ??
  (import.meta.env.DEV ? "" : "http://127.0.0.1:10713");

async function callApi(
  endpoint: string,
  body: Record<string, unknown>,
): Promise<unknown> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (e) {
    const hint =
      "Backend unreachable — start web\\start.bat (port 10713) and ensure gh auth login.";
    throw new Error(e instanceof Error ? `${e.message}. ${hint}` : hint);
  }
  if (!res.ok) {
    let detail = "";
    try {
      const errBody = (await res.json()) as { detail?: string; error?: string };
      detail = errBody.detail ?? errBody.error ?? "";
    } catch {
      /* ignore */
    }
    throw new Error(
      detail ? `HTTP ${res.status}: ${detail}` : `HTTP ${res.status}`,
    );
  }
  return res.json();
}

export async function gitOps(
  operation: string,
  args: Record<string, unknown> = {},
): Promise<unknown> {
  return callApi("/api/git", { operation, ...args });
}

export async function githubOps(
  operation: string,
  args: Record<string, unknown> = {},
): Promise<unknown> {
  return callApi("/api/github", { operation, ...args });
}

/** Preset GitHub discovery via HTTP bridge — fallback when MCP sampling unavailable; prefer git_github_search_workflow in full-sampling clients (e.g. Antigravity). */
export async function runDiscoveryWorkflow(
  args: Record<string, unknown>,
): Promise<unknown> {
  return callApi("/api/discovery", args);
}

export async function getStatus(): Promise<unknown> {
  const res = await fetch(`${BASE}/api/status`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const raw = (await res.json()) as {
    result?: {
      git?: { available?: boolean; version?: string };
      gh?: { available?: boolean; auth?: string; version?: string };
    };
  };
  if (raw?.result?.git || raw?.result?.gh) {
    const g = raw.result.git ?? {};
    const h = raw.result.gh ?? {};
    return {
      ...raw,
      git_available: g.available,
      gh_available: h.available,
      gh_authenticated: h.auth === "ok",
      git_version: g.version,
      gh_version: h.version,
    };
  }
  return raw;
}

/** Fleet morning digest — same as fleet_morning_digest MCP tool. */
export async function runMorningDigest(
  args: Record<string, unknown> = {},
): Promise<unknown> {
  return callApi("/api/morning-digest", args);
}

/** Single fleet_ops operation — same as fleet_ops MCP tool. */
export async function runFleetOps(
  operation: string,
  args: Record<string, unknown> = {},
): Promise<unknown> {
  return callApi("/api/fleet-ops", { operation, ...args });
}

/** CI diagnose — send a failed workflow log to the local LLM for root-cause. */
export async function runCiDiagnose(
  logText: string,
  context: Record<string, unknown> = {},
): Promise<unknown> {
  const messages = [
    {
      role: "user",
      content:
        "You are a CI failure diagnostician for a software fleet. " +
        "Analyse the failed workflow log below and answer:\n" +
        "1. ROOT CAUSE: what failed and why (1-3 sentences)\n" +
        "2. FIX: exact command or config change to repair it\n" +
        "3. VERIFY: how to confirm the fix\n" +
        "Be concrete. If the log is too short to diagnose, say so.\n\n" +
        `Repo context: ${JSON.stringify(context)}\n\nFailed log tail:\n\`\`\`\n${logText}\n\`\`\``,
    },
  ];
  const res = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, stream: false }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} diagnosing CI failure`);
  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");
  const decoder = new TextDecoder();
  let content = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    for (const line of chunk.split("\n")) {
      if (!line.trim()) continue;
      try {
        const ev = JSON.parse(line) as {
          type: string;
          content?: string;
          error?: string;
        };
        if (ev.type === "token" && ev.content) content += ev.content;
        if (ev.type === "error") throw new Error(ev.error ?? "LLM error");
      } catch {
        /* non-JSON chunk */
      }
    }
  }
  return { success: true, content };
}

/** Full fleet maintainer suite — morning digest + all fleet checks. */
export async function runFleetSuite(
  args: Record<string, unknown> = {},
): Promise<unknown> {
  return callApi("/api/fleet-suite", args);
}

export type FleetSuiteProgress = {
  percent: number;
  step: string;
  step_label: string;
  step_index: number;
  step_total: number;
  repo?: string;
  repo_index?: number;
  repo_total?: number;
  message?: string;
};

type FleetStreamEvent =
  | ({ type: "progress" } & FleetSuiteProgress)
  | { type: "done"; result?: unknown; success?: boolean; message?: string }
  | { type: "error"; error?: string };

function consumeFleetStreamLine(
  line: string,
  onProgress: (progress: FleetSuiteProgress) => void,
): "done" | "error" | null {
  if (!line.trim()) return null;
  const ev = JSON.parse(line) as FleetStreamEvent;
  if (ev.type === "progress") {
    onProgress(ev);
    return null;
  }
  if (ev.type === "error") {
    throw new Error(ev.error ?? "Fleet suite failed");
  }
  if (ev.type === "done") {
    return "done";
  }
  return null;
}

async function fetchLastFleetSuite(): Promise<unknown> {
  const res = await fetch(`${BASE}/api/fleet-suite/last`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} fetching fleet suite result`);
  }
  const body = (await res.json()) as { success?: boolean; error?: string };
  if (!body.success) {
    throw new Error(body.error ?? "Fleet suite result not available");
  }
  return body;
}

/** Stream full suite with live progress (NDJSON). */
export async function runFleetSuiteStream(
  args: Record<string, unknown>,
  onProgress: (progress: FleetSuiteProgress) => void,
): Promise<unknown> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/fleet-suite/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(args),
    });
  } catch (e) {
    const hint =
      "Backend unreachable — start web\\start.bat (port 10713) and ensure gh auth login.";
    throw new Error(e instanceof Error ? `${e.message}. ${hint}` : hint);
  }
  if (!res.ok || !res.body) {
    throw new Error(`HTTP ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let streamDone = false;

  while (true) {
    const { done, value } = await reader.read();
    if (value) {
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        if (consumeFleetStreamLine(line, onProgress) === "done") {
          streamDone = true;
        }
      }
    }
    if (done) {
      buffer += decoder.decode(undefined, { stream: false });
      if (
        buffer.trim() &&
        consumeFleetStreamLine(buffer, onProgress) === "done"
      ) {
        streamDone = true;
      }
      break;
    }
  }

  if (!streamDone) {
    throw new Error("Fleet suite stream ended without completion");
  }
  return fetchLastFleetSuite();
}
