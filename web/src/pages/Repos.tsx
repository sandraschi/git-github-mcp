import { useState, useEffect } from 'react'
import { Github, ExternalLink } from 'lucide-react'
import { api } from '../api/client'

interface Repo {
  name: string
  owner: { login: string }
  nameWithOwner?: string
  url?: string
  description?: string
}

export function Repos() {
  const [repos, setRepos] = useState<Repo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.github.repos().then((res) => {
      setLoading(false)
      const data = res as { success: boolean; repos?: Repo[]; error?: string }
      if (data.success && data.repos) {
        setRepos(data.repos)
      } else {
        setError(data.error || 'Failed to load repos')
      }
    })
  }, [])

  if (loading) return <div className="text-slate-400">Loading repos...</div>
  if (error) return <div className="text-red-400">{error}</div>

  return (
    <div className="space-y-6">
      <div className="text-slate-400 text-sm">{repos.length} repositories</div>

      <div className="grid gap-4">
        {repos.map((repo) => (
          <a
            key={repo.nameWithOwner || repo.name}
            href={repo.url || `https://github.com/${repo.owner?.login || 'user'}/${repo.name}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-4 p-4 rounded-xl bg-[#12121a] border border-[#1e1e2e] hover:border-indigo-500/30 transition-colors group"
          >
            <Github className="w-6 h-6 text-slate-500 group-hover:text-indigo-400 shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="font-medium text-slate-200 truncate">
                {repo.nameWithOwner || `${repo.owner?.login}/${repo.name}`}
              </div>
              {repo.description && (
                <div className="text-sm text-slate-500 truncate mt-0.5">{repo.description}</div>
              )}
            </div>
            <ExternalLink className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 shrink-0" />
          </a>
        ))}
      </div>

      {repos.length === 0 && (
        <div className="text-center py-12 text-slate-500">No repos found. Run gh auth login.</div>
      )}
    </div>
  )
}
