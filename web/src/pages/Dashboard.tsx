import { useEffect, useState } from 'react';
import { GitBranch, GitCommit, AlertCircle, GitPullRequest, Terminal, Wifi, WifiOff } from 'lucide-react';
import { gitOps, githubOps, getStatus } from '@/lib/api';

interface StatusData { git_available?: boolean; gh_available?: boolean; gh_authenticated?: boolean; }
interface RepoStatus { success: boolean; data?: { branch: string; remote_url: string; total_changes: number } }
interface LogData { success: boolean; data?: { count: number; entries: Array<{ hash: string; author: string; date: string; subject: string }> } }

export function Dashboard() {
  const [sysStatus, setSysStatus] = useState<StatusData | null>(null);
  const [repoStatus, setRepoStatus] = useState<RepoStatus | null>(null);
  const [recentLog, setRecentLog] = useState<LogData | null>(null);
  const [myRepos, setMyRepos] = useState<{ name: string; url: string; stargazerCount: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [repoPath, setRepoPath] = useState('D:/Dev/repos/git-github-mcp');

  useEffect(() => {
    Promise.allSettled([
      getStatus().then(d => setSysStatus(d as StatusData)),
      (gitOps('status', { repo_path: repoPath }) as Promise<RepoStatus>).then(setRepoStatus),
      (gitOps('log', { repo_path: repoPath, max_count: 5 }) as Promise<LogData>).then(setRecentLog),
      (githubOps('repo_list', { limit: 5 }) as Promise<{ repos: typeof myRepos }>)
        .then(d => setMyRepos(d?.repos ?? [])).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [repoPath]);

  const online = sysStatus?.git_available;
  const ghAuth = sysStatus?.gh_authenticated;

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" style={{ fontFamily: 'var(--font-ui)', color: 'var(--text)' }}>
            Dashboard
          </h1>
          <p className="text-sm mt-0.5" style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            git·github·mcp — unified developer ops
          </p>
        </div>
        <div className="flex items-center gap-2">
          {online
            ? <span className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--green)' }}><Wifi size={12} />git ok</span>
            : <span className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--red)' }}><WifiOff size={12} />git missing</span>
          }
          <span style={{ color: 'var(--border-2)' }}>·</span>
          <span className={`text-xs ${ghAuth ? 'text-green-400' : 'text-amber-400'}`}>
            gh {ghAuth ? 'authed' : 'not authed'}
          </span>
        </div>
      </div>

      {/* Repo path selector */}
      <div className="flex items-center gap-2 p-2 rounded" style={{ background: 'var(--bg-2)', border: '1px solid var(--border)' }}>
        <Terminal size={13} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
        <input
          className="flex-1 bg-transparent text-xs outline-none mono"
          style={{ color: 'var(--green)', caretColor: 'var(--green)' }}
          value={repoPath}
          onChange={e => setRepoPath(e.target.value)}
          onBlur={() => { setLoading(true); /* re-trigger effect */ }}
          placeholder="repo path..."
        />
      </div>

      {/* Status cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Branch', value: repoStatus?.data?.branch ?? '—', icon: GitBranch, color: 'var(--green)' },
          { label: 'Uncommitted', value: repoStatus?.data?.total_changes ?? '—', icon: AlertCircle, color: 'var(--amber)' },
          { label: 'Recent Commits', value: recentLog?.data?.count ?? '—', icon: GitCommit, color: 'var(--blue)' },
          { label: 'GH Repos', value: myRepos.length || '—', icon: GitPullRequest, color: 'var(--purple)' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="p-4 rounded scanline" style={{ background: 'var(--bg-2)', border: '1px solid var(--border)' }}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{label}</span>
              <Icon size={13} style={{ color }} />
            </div>
            <div className="text-xl font-bold mono" style={{ color }}>{loading ? '…' : String(value)}</div>
          </div>
        ))}
      </div>

      {/* Recent commits */}
      <div className="rounded" style={{ background: 'var(--bg-2)', border: '1px solid var(--border)' }}>
        <div className="px-4 py-3 flex items-center gap-2" style={{ borderBottom: '1px solid var(--border)' }}>
          <GitCommit size={13} style={{ color: 'var(--green)' }} />
          <span className="text-sm font-semibold">Recent Commits</span>
          <span className="ml-auto mono text-xs" style={{ color: 'var(--text-dim)' }}>{repoPath.split('/').pop()}</span>
        </div>
        <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
          {loading ? (
            <div className="p-6 text-center mono text-xs" style={{ color: 'var(--text-dim)' }}>loading…</div>
          ) : recentLog?.data?.entries?.length ? (
            recentLog.data.entries.map((e, i) => (
              <div key={i} className="flex items-center gap-3 px-4 py-2.5 hover:bg-white/[0.02] transition-colors">
                <span className="hash-chip shrink-0">{e.hash.slice(0, 7)}</span>
                <span className="flex-1 text-sm truncate" style={{ color: 'var(--text)' }}>{e.subject}</span>
                <span className="text-xs shrink-0" style={{ color: 'var(--text-dim)' }}>{e.author.split(' ')[0]}</span>
                <span className="text-xs mono shrink-0" style={{ color: 'var(--text-dim)' }}>{e.date}</span>
              </div>
            ))
          ) : (
            <div className="p-6 text-center text-xs" style={{ color: 'var(--text-dim)' }}>
              {recentLog?.success === false ? 'Not a git repo or API unreachable' : 'No commits'}
            </div>
          )}
        </div>
      </div>

      {/* GitHub repos */}
      {myRepos.length > 0 && (
        <div className="rounded" style={{ background: 'var(--bg-2)', border: '1px solid var(--border)' }}>
          <div className="px-4 py-3 flex items-center gap-2" style={{ borderBottom: '1px solid var(--border)' }}>
            <GitBranch size={13} style={{ color: 'var(--purple)' }} />
            <span className="text-sm font-semibold">Your GitHub Repos</span>
          </div>
          <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
            {myRepos.map((r, i) => (
              <div key={i} className="flex items-center gap-3 px-4 py-2.5 hover:bg-white/[0.02] transition-colors">
                <div className="h-1.5 w-1.5 rounded-full pulse-green" style={{ background: 'var(--green)', flexShrink: 0 }} />
                <span className="flex-1 mono text-sm" style={{ color: 'var(--text)' }}>{r.name}</span>
                <span className="text-xs mono" style={{ color: 'var(--text-dim)' }}>★ {r.stargazerCount}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
