/** Shared API client — calls the FastAPI bridge at :10702 */

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:10702';

async function callApi(endpoint: string, body: Record<string, unknown>): Promise<unknown> {
  const res = await fetch(`${BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function gitOps(operation: string, args: Record<string, unknown> = {}): Promise<unknown> {
  return callApi('/api/git', { operation, ...args });
}

export async function githubOps(operation: string, args: Record<string, unknown> = {}): Promise<unknown> {
  return callApi('/api/github', { operation, ...args });
}

/** Preset GitHub discovery via HTTP bridge — fallback when MCP sampling unavailable; prefer git_github_search_workflow in full-sampling clients (e.g. Antigravity). */
export async function runDiscoveryWorkflow(args: Record<string, unknown>): Promise<unknown> {
  return callApi('/api/discovery', args);
}

export async function getStatus(): Promise<unknown> {
  const res = await fetch(`${BASE}/api/status`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/** Fleet morning digest — same as fleet_morning_digest MCP tool. */
export async function runMorningDigest(args: Record<string, unknown> = {}): Promise<unknown> {
  return callApi('/api/morning-digest', args);
}
