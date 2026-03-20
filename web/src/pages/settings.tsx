import { useEffect, useState } from 'react';
import { CheckCircle, XCircle, Terminal, Loader2 } from 'lucide-react';
import { getStatus } from '@/lib/api';

interface Status {
  git_available?: boolean; gh_available?: boolean;
  gh_authenticated?: boolean; git_version?: string; gh_version?: string;
}

export function Settings() {
  const [status, setStatus] = useState<Status | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (getStatus() as Promise<Status>)
      .then(setStatus).catch(() => setStatus({}))
      .finally(() => setLoading(false));
  }, []);

  const Row = ({ label, ok, detail }: { label: string; ok?: boolean; detail?: string }) => (
    <div className="flex items-center gap-3 py-2.5 px-4"
      style={{ borderBottom: '1px solid var(--border)' }}>
      {ok
        ? <CheckCircle size={14} style={{ color: 'var(--green)', flexShrink: 0 }} />
        : <XCircle size={14} style={{ color: 'var(--red)', flexShrink: 0 }} />}
      <span className="text-sm flex-1">{label}</span>
      {detail && <span className="mono text-xs" style={{ color: 'var(--text-dim)' }}>{detail}</span>}
    </div>
  );

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* System status */}
      <div className="rounded overflow-hidden" style={{ border: '1px solid var(--border)' }}>
        <div className="flex items-center gap-2 px-4 py-3" style={{ background: 'var(--bg-2)', borderBottom: '1px solid var(--border)' }}>
          <Terminal size={13} style={{ color: 'var(--green)' }} />
          <span className="text-sm font-semibold">System Status</span>
        </div>
        {loading ? (
          <div className="flex justify-center py-8"><Loader2 className="animate-spin" size={18} style={{ color: 'var(--text-dim)' }} /></div>
        ) : (
          <div style={{ background: 'var(--bg-2)' }}>
            <Row label="git CLI" ok={status?.git_available} detail={status?.git_version} />
            <Row label="gh CLI" ok={status?.gh_available} detail={status?.gh_version} />
            <div className="flex items-center gap-3 py-2.5 px-4">
              {status?.gh_authenticated
                ? <CheckCircle size={14} style={{ color: 'var(--green)', flexShrink: 0 }} />
                : <XCircle size={14} style={{ color: 'var(--amber)', flexShrink: 0 }} />}
              <span className="text-sm flex-1">gh authenticated</span>
              {!status?.gh_authenticated && (
                <span className="mono text-xs" style={{ color: 'var(--amber)' }}>run: gh auth login</span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="rounded p-4 space-y-2" style={{ background: 'var(--bg-2)', border: '1px solid var(--border)' }}>
        <p className="text-sm font-semibold">About</p>
        <div className="mono text-xs space-y-1" style={{ color: 'var(--text-muted)' }}>
          <div><span style={{ color: 'var(--text-dim)' }}>version     </span>0.2.0</div>
          <div><span style={{ color: 'var(--text-dim)' }}>fastmcp     </span>3.1+</div>
          <div><span style={{ color: 'var(--text-dim)' }}>mcp port    </span>stdio (Claude Desktop)</div>
          <div><span style={{ color: 'var(--text-dim)' }}>web port    </span>10702</div>
          <div><span style={{ color: 'var(--text-dim)' }}>git ops     </span>30 actions</div>
          <div><span style={{ color: 'var(--text-dim)' }}>github ops  </span>25 actions</div>
          <div><span style={{ color: 'var(--text-dim)' }}>repo        </span>
            <a href="https://github.com/sandraschi/git-github-mcp" target="_blank" rel="noreferrer"
              className="hover:underline" style={{ color: 'var(--blue)' }}>
              sandraschi/git-github-mcp
            </a>
          </div>
        </div>
      </div>

      {/* gh auth reminder */}
      {!status?.gh_authenticated && !loading && (
        <div className="rounded p-4" style={{ background: 'rgba(245,158,11,0.05)', border: '1px solid rgba(245,158,11,0.2)' }}>
          <p className="text-sm font-semibold mb-2" style={{ color: 'var(--amber)' }}>GitHub not authenticated</p>
          <p className="mono text-xs" style={{ color: 'var(--text-muted)' }}>
            Run <span className="text-white">gh auth login</span> in a terminal to enable GitHub features.
            Issues, PRs, releases and workflow operations require this.
          </p>
        </div>
      )}
    </div>
  );
}
