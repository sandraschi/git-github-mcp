import { useEffect, useState, useCallback } from 'react';
import { BookOpen, Star, Lock, Globe, Loader2, RefreshCw, ExternalLink, GitBranch } from 'lucide-react';
import { githubOps, gitOps } from '@/lib/api';

interface GHRepo {
  name: string; description: string; isPrivate: boolean;
  stargazerCount: number; url: string; updatedAt: string;
  defaultBranchRef?: { name: string };
}
interface LocalStatus {
  success: boolean;
  data?: { branch: string; remote_url: string; has_changes: boolean; total_changes: number };
}

export function Repositories() {
  const [ghRepos, setGhRepos]     = useState<GHRepo[]>([]);
  const [localStatus, setLocal]   = useState<LocalStatus | null>(null);
  const [repoPath, setRepoPath]   = useState('D:/Dev/repos/git-github-mcp');
  const [loading, setLoading]     = useState(false);
  const [filter, setFilter]       = useState('');

  const load = useCallback(() => {
    setLoading(true);
    Promise.allSettled([
      (githubOps('repo_list', { limit: 50 }) as Promise<{ result: { repos: GHRepo[] } }>)
        .then(d => setGhRepos(d?.result?.repos ?? [])).catch(() => {}),
      (gitOps('status', { repo_path: repoPath }) as Promise<{ result: LocalStatus }>)
        .then(d => { if (d) setLocal({ success: true, data: (d.result as any) }); }).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [repoPath]);

  useEffect(load, [load]);

  const filtered = ghRepos.filter(r =>
    !filter || r.name.toLowerCase().includes(filter.toLowerCase()) ||
    (r.description ?? '').toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="space-y-5 max-w-5xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Repositories</h1>
        <button onClick={load} className="p-1.5 rounded" style={{ border: '1px solid var(--border)', color: 'var(--text-muted)' }}>
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Local repo status */}
      <div className="rounded p-4" style={{ background: 'var(--bg-2)', border: '1px solid var(--border)' }}>
        <div className="flex items-center gap-2 mb-3">
          <GitBranch size={13} style={{ color: 'var(--green)' }} />
          <span className="text-sm font-semibold">Local Working Repo</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="mono text-xs" style={{ color: 'var(--text-dim)' }}>$</span>
          <input
            className="flex-1 bg-transparent mono text-xs outline-none"
            style={{ color: 'var(--green)' }}
            value={repoPath}
            onChange={e => setRepoPath(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && load()}
            placeholder="repo path..."
          />
        </div>
        {localStatus?.success && localStatus.data && (
          <div className="flex items-center gap-4 mt-3 flex-wrap">
            <span className="mono text-xs flex items-center gap-1.5">
              <span style={{ color: 'var(--text-dim)' }}>branch</span>
              <span className="hash-chip">{localStatus.data.branch}</span>
            </span>
            <span className="mono text-xs flex items-center gap-1.5">
              <span style={{ color: 'var(--text-dim)' }}>changes</span>
              <span style={{ color: localStatus.data.has_changes ? 'var(--amber)' : 'var(--green)' }}>
                {localStatus.data.total_changes}
              </span>
            </span>
            {localStatus.data.remote_url && (
              <span className="mono text-xs truncate max-w-xs" style={{ color: 'var(--text-dim)' }}>
                {localStatus.data.remote_url}
              </span>
            )}
          </div>
        )}
        {localStatus?.success === false && (
          <p className="mono text-xs mt-2" style={{ color: 'var(--red)' }}>Not a git repo or API offline</p>
        )}
      </div>

      {/* GitHub repos */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <input
            className="flex-1 bg-transparent mono text-xs px-3 py-1.5 rounded outline-none"
            style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', color: 'var(--text)' }}
            value={filter} onChange={e => setFilter(e.target.value)}
            placeholder="filter repos..."
          />
          <span className="mono text-xs" style={{ color: 'var(--text-dim)' }}>
            {filtered.length} / {ghRepos.length}
          </span>
        </div>

        {loading && ghRepos.length === 0 ? (
          <div className="flex justify-center py-12">
            <Loader2 className="animate-spin" size={20} style={{ color: 'var(--green)' }} />
          </div>
        ) : ghRepos.length === 0 ? (
          <div className="p-8 text-center text-sm rounded" style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', color: 'var(--text-dim)' }}>
            No repos — ensure <span className="mono text-white">gh auth login</span> is run
          </div>
        ) : (
          <div className="grid gap-2 md:grid-cols-2">
            {filtered.map(r => (
              <div key={r.name} className="rounded p-4 group hover:border-slate-600 transition-colors"
                style={{ background: 'var(--bg-2)', border: '1px solid var(--border)' }}>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <BookOpen size={13} style={{ color: 'var(--blue)', flexShrink: 0 }} />
                    <span className="mono text-sm font-semibold truncate" style={{ color: 'var(--text)' }}>{r.name}</span>
                    {r.isPrivate
                      ? <Lock size={10} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
                      : <Globe size={10} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />}
                  </div>
                  <a href={r.url} target="_blank" rel="noreferrer"
                    className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                    <ExternalLink size={12} style={{ color: 'var(--text-dim)' }} />
                  </a>
                </div>
                {r.description && (
                  <p className="text-xs mt-1.5 line-clamp-2" style={{ color: 'var(--text-muted)' }}>{r.description}</p>
                )}
                <div className="flex items-center gap-3 mt-2">
                  <span className="mono text-xs flex items-center gap-1" style={{ color: 'var(--text-dim)' }}>
                    <Star size={10} />{r.stargazerCount}
                  </span>
                  {r.defaultBranchRef && (
                    <span className="hash-chip">{r.defaultBranchRef.name}</span>
                  )}
                  <span className="mono text-xs ml-auto" style={{ color: 'var(--text-dim)' }}>
                    {new Date(r.updatedAt).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
