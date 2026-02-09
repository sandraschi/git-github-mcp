import { useState } from 'react'
import { GitPullRequest, Plus } from 'lucide-react'
import { api } from '../api/client'

interface PR {
  number: number
  title: string
  state: string
  url?: string
}

export function PRs() {
  const [owner, setOwner] = useState('')
  const [repo, setRepo] = useState('')
  const [prs, setPrs] = useState<PR[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [createOwner, setCreateOwner] = useState('')
  const [createRepo, setCreateRepo] = useState('')
  const [createTitle, setCreateTitle] = useState('')
  const [createBody, setCreateBody] = useState('')
  const [creating, setCreating] = useState(false)

  const handleList = () => {
    if (!owner || !repo) return
    setLoading(true)
    setError(null)
    api.github.prs(owner, repo).then((res) => {
      setLoading(false)
      const data = res as { success: boolean; result?: { prs: PR[] }; error?: string }
      if (data.success && data.result?.prs) {
        setPrs(data.result.prs)
      } else {
        setError(data.error || 'Failed')
      }
    })
  }

  const handleCreate = () => {
    if (!createOwner || !createRepo || !createTitle) return
    setCreating(true)
    api.github.ops({
      operation: 'create_pr',
      owner: createOwner,
      repo: createRepo,
      title: createTitle,
      body: createBody || undefined,
    }).then((res) => {
      setCreating(false)
      if (res.success) {
        setCreateTitle('')
        setCreateBody('')
        if (createOwner && createRepo) {
          setOwner(createOwner)
          setRepo(createRepo)
          api.github.prs(createOwner, createRepo).then((r) => {
            const d = r as { success: boolean; result?: { prs: PR[] } }
            if (d.success && d.result?.prs) setPrs(d.result.prs)
          })
        }
      } else {
        setError((res as { error?: string }).error || 'Failed')
      }
    })
  }

  return (
    <div className="space-y-8">
      <div className="p-6 rounded-xl bg-[#12121a] border border-[#1e1e2e]">
        <h3 className="font-semibold text-slate-200 mb-4">List PRs</h3>
        <div className="flex flex-wrap gap-3">
          <input
            placeholder="owner"
            value={owner}
            onChange={(e) => setOwner(e.target.value)}
            className="px-4 py-2 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] text-slate-200 placeholder-slate-500 focus:border-indigo-500/50 outline-none w-32"
          />
          <input
            placeholder="repo"
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
            className="px-4 py-2 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] text-slate-200 placeholder-slate-500 focus:border-indigo-500/50 outline-none w-40"
          />
          <button
            onClick={handleList}
            disabled={loading}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50 transition-colors font-medium"
          >
            {loading ? 'Loading...' : 'List'}
          </button>
        </div>
      </div>

      <div className="p-6 rounded-xl bg-[#12121a] border border-[#1e1e2e]">
        <h3 className="font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <Plus size={18} /> Create PR
        </h3>
        <div className="space-y-3">
          <div className="flex gap-3">
            <input
              placeholder="owner"
              value={createOwner}
              onChange={(e) => setCreateOwner(e.target.value)}
              className="px-4 py-2 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] text-slate-200 placeholder-slate-500 focus:border-indigo-500/50 outline-none w-32"
            />
            <input
              placeholder="repo"
              value={createRepo}
              onChange={(e) => setCreateRepo(e.target.value)}
              className="px-4 py-2 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] text-slate-200 placeholder-slate-500 focus:border-indigo-500/50 outline-none w-40"
            />
          </div>
          <input
            placeholder="Title"
            value={createTitle}
            onChange={(e) => setCreateTitle(e.target.value)}
            className="w-full px-4 py-2 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] text-slate-200 placeholder-slate-500 focus:border-indigo-500/50 outline-none"
          />
          <textarea
            placeholder="Body (optional)"
            value={createBody}
            onChange={(e) => setCreateBody(e.target.value)}
            rows={3}
            className="w-full px-4 py-2 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] text-slate-200 placeholder-slate-500 focus:border-indigo-500/50 outline-none resize-none"
          />
          <button
            onClick={handleCreate}
            disabled={creating}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50 transition-colors font-medium"
          >
            {creating ? 'Creating...' : 'Create PR'}
          </button>
        </div>
      </div>

      {error && <div className="text-red-400">{error}</div>}

      <div className="space-y-3">
        {prs.map((pr) => (
          <a
            key={pr.number}
            href={pr.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-4 p-4 rounded-xl bg-[#12121a] border border-[#1e1e2e] hover:border-indigo-500/30 transition-colors group"
          >
            <GitPullRequest className="w-5 h-5 text-slate-500 shrink-0" />
            <span className="text-slate-400 text-sm w-12">#{pr.number}</span>
            <span className="flex-1 font-medium text-slate-200 truncate">{pr.title}</span>
            <span className={`text-xs px-2 py-0.5 rounded ${pr.state === 'open' ? 'bg-green-500/20 text-green-400' : 'bg-slate-700 text-slate-400'}`}>
              {pr.state}
            </span>
          </a>
        ))}
      </div>
    </div>
  )
}
