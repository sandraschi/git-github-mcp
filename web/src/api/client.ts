const API_BASE = (import.meta as { env?: { VITE_API_BASE_URL?: string } }).env?.VITE_API_BASE_URL || ''

export interface ApiResponse<T = unknown> {
  success: boolean
  result?: T
  error?: string
  message?: string
  execution_time_ms?: number
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  const url = `${API_BASE}${endpoint}`
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      signal: AbortSignal.timeout(60000),
      ...options,
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || data.message || `HTTP ${res.status}`)
    return data
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : 'Request failed',
    }
  }
}

export const api = {
  git: {
    ops: (body: Record<string, unknown>) =>
      request<Record<string, unknown>>('/api/v1/git/ops', { method: 'POST', body: JSON.stringify(body) }),
  },
  github: {
    ops: (body: Record<string, unknown>) =>
      request<Record<string, unknown>>('/api/v1/github/ops', { method: 'POST', body: JSON.stringify(body) }),
    repos: () => request<{ repos: unknown[] }>('/api/v1/github/repos'),
    issues: (owner: string, repo: string, state = 'open') =>
      request<{ issues: unknown[] }>(`/api/v1/github/issues?owner=${owner}&repo=${repo}&state=${state}`),
    prs: (owner: string, repo: string, state = 'open') =>
      request<{ prs: unknown[] }>(`/api/v1/github/prs?owner=${owner}&repo=${repo}&state=${state}`),
  },
  glama: {
    check: (owner: string, repo: string) =>
      request<GlamaCheckResult>(`/api/v1/glama/check?owner=${encodeURIComponent(owner)}&repo=${encodeURIComponent(repo)}`),
  },
}

export interface GlamaCheckResult {
  success: boolean
  exists?: boolean
  owner?: string
  repo?: string
  url?: string | null
  name?: string
  description?: string
  license?: string
  attributes?: string[]
  glama_id?: string
  message?: string
  error?: string
}
