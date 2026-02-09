import { useState, useEffect } from 'react'
import { ExternalLink, CheckCircle, XCircle, Loader2, RefreshCw } from 'lucide-react'
import { api, type GlamaCheckResult } from '../api/client'

interface Repo {
  name: string
  owner: { login: string }
  nameWithOwner?: string
  url?: string
  description?: string
}

interface RepoGlamaState {
  repo: Repo
  status: 'loading' | 'listed' | 'not_listed' | 'error'
  data?: GlamaCheckResult
}

const MCP_REPO_PATTERNS = ['mcp', 'mcpb'] as const

function isMcpRepo(name: string): boolean {
  const lower = name.toLowerCase()
  return MCP_REPO_PATTERNS.some((p) => lower.includes(p))
}

export function Glama() {
  const [repos, setRepos] = useState<Repo[]>([])
  const [states, setStates] = useState<RepoGlamaState[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [checkTrigger, setCheckTrigger] = useState(0)

  useEffect(() => {
    api.github.repos().then((res) => {
      const data = res as { success: boolean; repos?: Repo[]; error?: string }
      if (data.success && data.repos) {
        const mcpRepos = data.repos.filter((r) => isMcpRepo(r.name))
        setRepos(mcpRepos)
        setStates(mcpRepos.map((repo) => ({ repo, status: 'loading' as const })))
        setCheckTrigger((t) => t + 1)
      } else {
        setError(data.error || 'Failed to load repos')
      }
      setLoading(false)
    })
  }, [])

  useEffect(() => {
    const toCheck = states.filter((s) => s.status === 'loading')
    if (toCheck.length === 0) return

    const checkAll = async () => {
      const results = await Promise.all(
        states.map(async (s) => {
          if (s.status !== 'loading') return s
          const owner = s.repo.owner?.login || 'unknown'
          const res = await api.glama.check(owner, s.repo.name)
          const data = res as GlamaCheckResult
          return {
            repo: s.repo,
            status: data.success
              ? data.exists
                ? ('listed' as const)
                : ('not_listed' as const)
              : ('error' as const),
            data,
          }
        })
      )
      setStates(results)
    }
    checkAll()
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only rerun when checkTrigger changes
  }, [checkTrigger])

  const handleRefresh = () => {
    setRefreshing(true)
    setStates(repos.map((repo) => ({ repo, status: 'loading' as const })))
    setCheckTrigger((t) => t + 1)
    setTimeout(() => setRefreshing(false), 500)
  }

  if (loading) return <div className="text-slate-400">Loading repos...</div>
  if (error) return <div className="text-red-400">{error}</div>

  const listed = states.filter((s) => s.status === 'listed')
  const notListed = states.filter((s) => s.status === 'not_listed')
  const errors = states.filter((s) => s.status === 'error')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-200">Glama.ai Listing Status</h2>
          <p className="text-sm text-slate-500 mt-1">
            Which of our MCP server repos have been scraped by Glama and their reviews
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 hover:bg-indigo-500/20 transition-colors disabled:opacity-50"
        >
          <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      <div className="flex gap-4 text-sm">
        <span className="text-green-400">{listed.length} listed</span>
        <span className="text-slate-500">{notListed.length} not scraped</span>
        {errors.length > 0 && <span className="text-amber-400">{errors.length} errors</span>}
      </div>

      <div className="grid gap-4">
        {states.map((s) => (
          <div
            key={s.repo.nameWithOwner || s.repo.name}
            className="p-4 rounded-xl bg-[#12121a] border border-[#1e1e2e] hover:border-indigo-500/20 transition-colors"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3">
                  {s.status === 'loading' && (
                    <Loader2 size={18} className="animate-spin text-slate-500 shrink-0" />
                  )}
                  {s.status === 'listed' && (
                    <CheckCircle size={18} className="text-green-500 shrink-0" />
                  )}
                  {s.status === 'not_listed' && (
                    <XCircle size={18} className="text-slate-500 shrink-0" />
                  )}
                  {s.status === 'error' && (
                    <XCircle size={18} className="text-amber-400 shrink-0" />
                  )}
                  <span className="font-medium text-slate-200">
                    {s.repo.nameWithOwner || `${s.repo.owner?.login}/${s.repo.name}`}
                  </span>
                </div>
                {s.data?.description && (
                  <p className="text-sm text-slate-500 mt-1 line-clamp-2">{s.data.description}</p>
                )}
                {s.data?.license && (
                  <span className="inline-block mt-2 text-xs text-slate-600 bg-slate-800/50 px-2 py-0.5 rounded">
                    {s.data.license}
                  </span>
                )}
              </div>
              <div className="shrink-0 flex items-center gap-2">
                {s.status === 'listed' && s.data?.url && (
                  <a
                    href={s.data.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 hover:bg-indigo-500/20 transition-colors text-sm"
                  >
                    View on Glama
                    <ExternalLink size={14} />
                  </a>
                )}
                {s.status === 'not_listed' && (
                  <a
                    href={`https://glama.ai/mcp/servers?query=author:${s.repo.owner?.login}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-slate-500 hover:text-slate-300 text-sm"
                  >
                    Search Glama
                    <ExternalLink size={14} />
                  </a>
                )}
                {s.repo.url && (
                  <a
                    href={s.repo.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-slate-500 hover:text-indigo-400"
                  >
                    <ExternalLink size={16} />
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {states.length === 0 && (
        <div className="text-center py-12 text-slate-500">
          No MCP repos found. Repos with "mcp" or "mcpb" in the name are shown.
        </div>
      )}
    </div>
  )
}
