import { useEffect, useState } from 'react';
import { GitBranch, GitCommit, AlertCircle, GitPullRequest, Terminal, Wifi, WifiOff, CircleDot } from 'lucide-react';
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
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h1 className="text-4xl font-heading font-black tracking-tighter uppercase text-foreground">
              Dashboard
            </h1>
            <div className="h-px w-12 bg-gh-green/30 mt-2" />
          </div>
          <p className="text-sm text-muted-foreground font-mono flex items-center gap-2">
            <Terminal className="w-3 h-3" />
            git·github·mcp — hardened orchestration substrate
          </p>
        </div>

        <div className="flex items-center gap-3 p-1 rounded-lg bg-white/5 border border-white/5 backdrop-blur-sm">
          <StatusBadge 
            label="GIT" 
            online={online} 
            icon={Wifi} 
            offIcon={WifiOff} 
            colorClass={online ? 'text-gh-green' : 'text-destructive'} 
          />
          <div className="w-px h-4 bg-white/10" />
          <StatusBadge 
            label="GH" 
            online={ghAuth} 
            icon={CircleDot} 
            offIcon={AlertCircle} 
            colorClass={ghAuth ? 'text-gh-blue' : 'text-amber-500'} 
          />
        </div>
      </div>

      {/* Repo Configuration */}
      <div className="group relative">
        <div className="absolute -inset-1 bg-gradient-to-r from-gh-green/20 to-gh-blue/20 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200" />
        <div className="relative flex items-center gap-4 p-4 rounded-xl glass-dark border-border/50">
          <Terminal className="w-4 h-4 text-gh-green" />
          <div className="flex-1 space-y-1">
            <label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 px-1">Active Context</label>
            <input
              className="w-full bg-transparent text-sm font-mono text-gh-green outline-none selection:bg-gh-green/20"
              value={repoPath}
              onChange={e => setRepoPath(e.target.value)}
              onBlur={() => { setLoading(true); }}
              placeholder="System path to local git repository..."
            />
          </div>
        </div>
      </div>

      {/* Analytics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard 
          label="Active Branch" 
          value={repoStatus?.data?.branch} 
          icon={GitBranch} 
          loading={loading}
          color="text-gh-green"
        />
        <MetricCard 
          label="Pending Sync" 
          value={repoStatus?.data?.total_changes} 
          icon={AlertCircle} 
          loading={loading}
          color="text-amber-500"
        />
        <MetricCard 
          label="Commit History" 
          value={recentLog?.data?.count} 
          icon={GitCommit} 
          loading={loading}
          color="text-gh-blue"
        />
        <MetricCard 
          label="Cloud Repos" 
          value={myRepos.length} 
          icon={GitPullRequest} 
          loading={loading}
          color="text-purple-400"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Commit Log */}
        <div className="lg:col-span-2 glass rounded-2xl overflow-hidden border-border/50">
          <div className="px-6 py-4 border-b border-white/5 bg-white/5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <GitCommit className="w-4 h-4 text-gh-green" />
              <h2 className="text-sm font-bold tracking-tight uppercase">Recent Changes</h2>
            </div>
            <span className="text-[10px] font-mono text-muted-foreground bg-black/40 px-2 py-0.5 rounded border border-white/5 uppercase">
              {repoPath.split('/').pop() || 'fs'}
            </span>
          </div>
          
          <div className="divide-y divide-white/5">
            {loading ? (
              <LoadingState />
            ) : recentLog?.data?.entries?.length ? (
              recentLog.data.entries.map((e, i) => (
                <div key={i} className="group flex items-center gap-4 px-6 py-3.5 hover:bg-gh-green/[0.03] transition-all">
                  <span className="font-mono text-[10px] font-bold text-gh-green bg-gh-green/10 px-2 py-1 rounded border border-gh-green/20 group-hover:border-gh-green/40 transition-all">
                    {e.hash.slice(0, 7)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-foreground/90 truncate group-hover:text-foreground transition-colors leading-tight">
                      {e.subject}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] text-muted-foreground capitalize">{e.author.split(' ')[0]}</span>
                      <div className="w-0.5 h-0.5 rounded-full bg-white/20" />
                      <span className="text-[10px] text-muted-foreground font-mono">{e.date}</span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <EmptyState message={recentLog?.success === false ? 'No Git repository detected' : 'Commit history is empty'} />
            )}
          </div>
        </div>

        {/* GitHub Fleet */}
        <div className="glass rounded-2xl overflow-hidden border-border/50">
          <div className="px-6 py-4 border-b border-white/5 bg-white/5 flex items-center gap-2">
            <CircleDot className="w-4 h-4 text-gh-blue" />
            <h2 className="text-sm font-bold tracking-tight uppercase">Cloud Fleet</h2>
          </div>
          
          <div className="divide-y divide-white/5 flex flex-col h-full">
            {myRepos.length > 0 ? (
              myRepos.map((r, i) => (
                <div key={i} className="flex items-center gap-3 px-6 py-4 hover:bg-gh-blue/[0.03] transition-all group">
                  <div className="h-2 w-2 rounded-full bg-gh-green shadow-[0_0_8px_rgba(34,197,94,0.4)] group-hover:scale-125 transition-transform" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-mono text-foreground truncate">{r.name}</p>
                    <div className="flex items-center gap-1.5 mt-0.5 text-[10px] text-muted-foreground">
                      <Wifi className="w-2.5 h-2.5" />
                      <span>Authenticated</span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="text-[10px] font-mono text-muted-foreground">★ {r.stargazerCount}</span>
                  </div>
                </div>
              ))
            ) : (
              <EmptyState message="No cloud repositories found" />
            )}
            <div className="flex-1 bg-black/20" />
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ label, online, icon: Icon, offIcon: OffIcon, colorClass }: { 
  label: string; 
  online?: boolean; 
  icon: React.ElementType; 
  offIcon: React.ElementType; 
  colorClass: string; 
}) {
  return (
    <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md transition-all ${online ? 'bg-white/5' : 'bg-destructive/10'}`}>
      {online ? <Icon className={`w-3 h-3 ${colorClass}`} /> : <OffIcon className="w-3 h-3 text-destructive" />}
      <span className={`text-[10px] font-bold uppercase tracking-tight ${online ? 'text-foreground/80' : 'text-destructive/80'}`}>
        {label}: {online ? 'OK' : 'FAIL'}
      </span>
    </div>
  );
}

function MetricCard({ label, value, icon: Icon, loading, color }: { 
  label: string; 
  value?: string | number; 
  icon: React.ElementType; 
  loading: boolean; 
  color: string; 
}) {
  return (
    <div className="glass p-5 rounded-2xl relative overflow-hidden group hover:border-gh-green/30 transition-all">
      <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
        <Icon className="w-12 h-12" />
      </div>
      <div className="flex flex-col gap-2">
        <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground/60">{label}</label>
        <div className={`text-2xl font-black font-mono tracking-tight flex items-center gap-2 ${color}`}>
          {loading ? (
            <div className="h-8 w-16 bg-white/5 animate-pulse rounded" />
          ) : (
            <span className="truncate">{String(value ?? '—')}</span>
          )}
          {!loading && value === 'main' && <div className="h-1.5 w-1.5 rounded-full bg-gh-green shadow-[0_0_8px_rgba(34,197,94,0.6)]" />}
        </div>
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="p-12 flex flex-col items-center justify-center gap-3">
      <div className="w-8 h-8 border-2 border-gh-green/20 border-t-gh-green rounded-full animate-spin" />
      <span className="text-xs font-mono text-muted-foreground uppercase tracking-widest">Aggregating...</span>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="p-12 flex flex-col items-center justify-center text-center">
      <AlertCircle className="w-8 h-8 text-muted-foreground/20 mb-3" />
      <p className="text-sm text-muted-foreground font-mono">{message}</p>
    </div>
  );
}
