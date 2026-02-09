import { useState } from 'react'
import { GitBranch, Github } from 'lucide-react'
import { api } from '../api/client'
import { logger } from '../utils/logger'

type ToolType = 'git' | 'github'

const GIT_OPS = ['clone', 'status', 'add', 'commit', 'push', 'pull', 'branch', 'tag', 'stash'] as const
const GITHUB_OPS = ['create_issue', 'list_issues', 'create_pr', 'list_prs', 'search'] as const

export function Tools() {
  const [toolType, setToolType] = useState<ToolType>('git')
  const [operation, setOperation] = useState<string>(GIT_OPS[0])
  const [params, setParams] = useState('{}')
  const [result, setResult] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const handleRun = () => {
    setLoading(true)
    setResult('')

    let body: Record<string, unknown> = { operation }
    try {
      const parsed = JSON.parse(params || '{}')
      body = { ...parsed, operation }
    } catch {
      logger.warn('Invalid JSON params', { params })
    }

    const call = toolType === 'git' ? api.git.ops : api.github.ops
    call(body).then((res) => {
      setLoading(false)
      setResult(JSON.stringify(res, null, 2))
      logger.info('Tool executed', { toolType, operation, success: res.success })
    })
  }

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-xl bg-[#12121a] border border-[#1e1e2e]">
        <h3 className="font-semibold text-slate-200 mb-4">Tool Runner</h3>

        <div className="flex gap-4 mb-4">
          <button
            onClick={() => { setToolType('git'); setOperation(GIT_OPS[0]) }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${toolType === 'git' ? 'bg-indigo-600 text-white' : 'bg-[#0a0a0f] text-slate-400 hover:text-slate-200 border border-[#1e1e2e]'}`}
          >
            <GitBranch size={18} /> git_ops
          </button>
          <button
            onClick={() => { setToolType('github'); setOperation(GITHUB_OPS[0]) }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${toolType === 'github' ? 'bg-indigo-600 text-white' : 'bg-[#0a0a0f] text-slate-400 hover:text-slate-200 border border-[#1e1e2e]'}`}
          >
            <Github size={18} /> github_ops
          </button>
        </div>

        <div className="mb-4">
          <label className="block text-sm text-slate-500 mb-2">Operation</label>
          <select
            value={operation}
            onChange={(e) => setOperation(e.target.value)}
            className="px-4 py-2 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] text-slate-200 focus:border-indigo-500/50 outline-none w-full"
          >
            {(toolType === 'git' ? GIT_OPS : GITHUB_OPS).map((op) => (
              <option key={op} value={op}>{op}</option>
            ))}
          </select>
        </div>

        <div className="mb-4">
          <label className="block text-sm text-slate-500 mb-2">Params (JSON)</label>
          <textarea
            value={params}
            onChange={(e) => setParams(e.target.value)}
            rows={6}
            placeholder='{"repo_path": ".", "message": "fix: ..."}'
            className="w-full px-4 py-2 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] text-slate-200 placeholder-slate-500 focus:border-indigo-500/50 outline-none font-mono text-sm resize-none"
          />
        </div>

        <button
          onClick={handleRun}
          disabled={loading}
          className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50 transition-colors font-medium"
        >
          {loading ? 'Running...' : 'Run'}
        </button>
      </div>

      {result && (
        <div className="p-6 rounded-xl bg-[#12121a] border border-[#1e1e2e]">
          <h3 className="font-semibold text-slate-200 mb-2">Result</h3>
          <pre className="text-sm text-slate-400 font-mono overflow-x-auto whitespace-pre-wrap break-all">
            {result}
          </pre>
        </div>
      )}
    </div>
  )
}
