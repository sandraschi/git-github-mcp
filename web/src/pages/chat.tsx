import { useState, useRef, useEffect } from 'react';
import { Bot, User, Send, Loader2, Terminal, Compass, Copy, Check } from 'lucide-react';
import { gitOps, githubOps, runDiscoveryWorkflow } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  error?: boolean;
}

const EXAMPLES = [
  'git status D:/Dev/repos/git-github-mcp',
  'git log --count 5',
  'github repos sandraschi',
  'github issues sandraschi git-github-mcp',
  'github prs sandraschi git-github-mcp',
  'github find-bak sandraschi',
  'github show sandraschi git-github-mcp',
  'github gitingest sandraschi git-github-mcp',
  'github gitingest-help',
  'github auth',
];

interface DiscoveryPresetMeta {
  id: string;
  title: string;
  blurb: string;
}

const DISCOVERY_PRESETS: DiscoveryPresetMeta[] = [
  { id: 'org_snapshot', title: 'Org snapshot', blurb: 'Verify gh auth, then list repos for an owner.' },
  { id: 'topic_hunt', title: 'Topic hunt', blurb: 'Find repos by GitHub topic (tag); optional owner/text filter.' },
  { id: 'code_sweep', title: 'Code sweep', blurb: 'Scoped code search; needs owner + query and/or file extension.' },
  { id: 'repo_deep_dive', title: 'Repo deep-dive', blurb: 'Card, open issues, open PRs, then a Gitingest link.' },
  { id: 'global_search', title: 'Global search', blurb: 'GitHub repo search with full query syntax.' },
];

/** Very simple natural-language → tool dispatcher */
async function dispatch(input: string): Promise<string> {
  const parts = input.trim().split(/\s+/);
  const cmd = parts[0]?.toLowerCase();

  if (cmd === 'git' || cmd === 'g') {
    const op = parts[1]?.toLowerCase();
    const repoPath = parts.find(p => p.includes('/') || p.includes('\\')) ?? undefined;
    switch (op) {
      case 'status': return JSON.stringify(await gitOps('status', { repo_path: repoPath }), null, 2);
      case 'log':    {
        const count = parseInt(parts.find(p => p.startsWith('--count=') || /^\d+$/.test(p)) ?? '10');
        return JSON.stringify(await gitOps('log', { repo_path: repoPath, max_count: isNaN(count) ? 10 : count }), null, 2);
      }
      case 'branches': return JSON.stringify(await gitOps('branch_list', { repo_path: repoPath }), null, 2);
      case 'diff':     return JSON.stringify(await gitOps('diff', { repo_path: repoPath }), null, 2);
      case 'stash':    return JSON.stringify(await gitOps('stash_list', { repo_path: repoPath }), null, 2);
      case 'tags':     return JSON.stringify(await gitOps('tag_list', { repo_path: repoPath }), null, 2);
      default:         return `Unknown git sub-command: ${op}\nTry: status, log, branches, diff, stash, tags`;
    }
  }

  if (cmd === 'github' || cmd === 'gh') {
    const op = parts[1]?.toLowerCase();
    const owner = parts[2];
    const repo  = parts[3];
    switch (op) {
      case 'repos':    return JSON.stringify(await githubOps('repo_list', { owner, limit: 20 }), null, 2);
      case 'issues':   return JSON.stringify(await githubOps('issue_list', { owner, repo, limit: 20 }), null, 2);
      case 'prs':      return JSON.stringify(await githubOps('pr_list', { owner, repo, limit: 20 }), null, 2);
      case 'releases': return JSON.stringify(await githubOps('release_list', { owner, repo }), null, 2);
      case 'find-bak': return JSON.stringify(await githubOps('code_find_repos', { owner, extension: 'bak', limit: 50 }), null, 2);
      case 'show':     return JSON.stringify(await githubOps('show_repo', { owner, repo, output_format: 'markdown' }), null, 2);
      case 'gitingest': return JSON.stringify(await githubOps('gitingest_link', { owner, repo }), null, 2);
      case 'gitingest-help': return JSON.stringify(await githubOps('gitingest_help'), null, 2);
      case 'gitingest-url': return JSON.stringify(await githubOps('gitingest_convert_url', { github_url: parts.slice(2).join(' ') }), null, 2);
      case 'search':   return JSON.stringify(await githubOps('search_repos', { query: parts.slice(2).join(' ') }), null, 2);
      case 'auth':     return JSON.stringify(await githubOps('auth_status'), null, 2);
      default:         return `Unknown github sub-command: ${op}\nTry: repos, issues, prs, releases, find-bak, show, gitingest, gitingest-help, gitingest-url, search, auth`;
    }
  }

  return `Unknown command: ${cmd}\n\nAvailable:\n  git status [path]\n  git log [--count N] [path]\n  git branches [path]\n  git diff [path]\n  git stash [path]\n  git tags [path]\n  github repos [owner]\n  github issues <owner> <repo>\n  github prs <owner> <repo>\n  github releases <owner> <repo>\n  github find-bak <owner>\n  github show <owner> <repo>\n  github gitingest <owner> <repo>\n  github gitingest-help\n  github gitingest-url <https://github.com/...>\n  github search <query>\n  github auth`;
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([{
    role: 'system',
    content: 'git·github·mcp command interface ready.\nType git or github commands, or pick an example below.',
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const [discPreset, setDiscPreset] = useState('org_snapshot');
  const [discOwner, setDiscOwner] = useState('');
  const [discRepo, setDiscRepo] = useState('');
  const [discQuery, setDiscQuery] = useState('');
  const [discTopic, setDiscTopic] = useState('');
  const [discExt, setDiscExt] = useState('');
  const [discLimit, setDiscLimit] = useState('25');
  const [discLoading, setDiscLoading] = useState(false);
  const [discResult, setDiscResult] = useState<string | null>(null);
  const [discCopied, setDiscCopied] = useState(false);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const send = async (text?: string) => {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;
    const ts = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages(m => [...m, { role: 'user', content: msg, timestamp: ts() }]);
    setInput('');
    setLoading(true);
    try {
      const result = await dispatch(msg);
      setMessages(m => [...m, { role: 'assistant', content: result, timestamp: ts() }]);
    } catch (e) {
      setMessages(m => [...m, { role: 'assistant', content: `Error: ${e}`, timestamp: ts(), error: true }]);
    } finally {
      setLoading(false);
    }
  };

  const runDiscovery = async () => {
    let lim = parseInt(discLimit, 10);
    if (Number.isNaN(lim)) lim = 25;
    setDiscLoading(true);
    setDiscCopied(false);
    setDiscResult(null);
    try {
      const raw = await runDiscoveryWorkflow({
        preset: discPreset,
        owner: discOwner.trim() || undefined,
        repo: discRepo.trim() || undefined,
        query: discQuery.trim() || undefined,
        topic: discTopic.trim() || undefined,
        extension: discExt.trim() || undefined,
        limit: lim,
      });
      setDiscResult(JSON.stringify(raw, null, 2));
    } catch (e) {
      setDiscResult(JSON.stringify({ success: false, error: String(e) }, null, 2));
    } finally {
      setDiscLoading(false);
    }
  };

  const copyDiscovery = async () => {
    if (!discResult) return;
    try {
      await navigator.clipboard.writeText(discResult);
      setDiscCopied(true);
      setTimeout(() => setDiscCopied(false), 2000);
    } catch {
      setDiscCopied(false);
    }
  };

  const presetMeta = DISCOVERY_PRESETS.find(p => p.id === discPreset);

  return (
    <div className="flex flex-col max-w-6xl" style={{ height: 'calc(100vh - 5rem)' }}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold">Command</h1>
          <p className="text-xs mt-0.5 mono" style={{ color: 'var(--text-muted)' }}>
            direct git + github tool interface
          </p>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-4 flex-1 min-h-0">
      {/* Message area */}
      <div className="flex flex-col flex-1 min-w-0 min-h-0">
      <div className="flex-1 overflow-y-auto rounded space-y-1 p-3 mb-3"
        style={{ background: 'var(--bg-2)', border: '1px solid var(--border)' }}>
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-2 ${m.role === 'user' ? 'justify-end' : ''}`}>
            {m.role !== 'user' && (
              <div className="h-6 w-6 rounded flex items-center justify-center shrink-0 mt-0.5"
                style={{ background: m.role === 'system' ? 'var(--bg-3)' : 'rgba(34,197,94,0.1)', border: '1px solid var(--border)' }}>
                {m.role === 'system'
                  ? <Terminal size={11} style={{ color: 'var(--text-dim)' }} />
                  : <Bot size={11} style={{ color: 'var(--green)' }} />}
              </div>
            )}
            <div className={`max-w-[80%] ${m.role === 'user' ? 'items-end' : 'items-start'} flex flex-col gap-0.5`}>
              <pre
                className="mono text-xs rounded p-3 whitespace-pre-wrap break-all"
                style={{
                  background: m.role === 'user' ? 'var(--bg-3)' : 'var(--bg)',
                  border: `1px solid ${m.error ? 'rgba(239,68,68,0.3)' : 'var(--border)'}`,
                  color: m.error ? 'var(--red)' : m.role === 'user' ? 'var(--cyan)' : 'var(--text)',
                  maxHeight: 400, overflowY: 'auto',
                }}>
                {m.content}
              </pre>
              <span className="text-xs" style={{ color: 'var(--text-dim)' }}>{m.timestamp}</span>
            </div>
            {m.role === 'user' && (
              <div className="h-6 w-6 rounded flex items-center justify-center shrink-0 mt-0.5"
                style={{ background: 'var(--bg-3)', border: '1px solid var(--border)' }}>
                <User size={11} style={{ color: 'var(--text-muted)' }} />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 px-2 py-1">
            <Loader2 size={12} className="animate-spin" style={{ color: 'var(--green)' }} />
            <span className="mono text-xs" style={{ color: 'var(--text-dim)' }}>executing…</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Examples */}
      <div className="flex gap-1.5 flex-wrap mb-2">
        {EXAMPLES.map(ex => (
          <button key={ex} onClick={() => send(ex)}
            className="mono text-xs px-2 py-1 rounded transition-colors hover:border-slate-600"
            style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', color: 'var(--text-dim)' }}>
            {ex}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="flex items-center gap-2 px-3 py-2 rounded"
        style={{ background: 'var(--bg-2)', border: '1px solid var(--border-2)' }}>
        <span className="mono text-xs shrink-0" style={{ color: 'var(--green)' }}>❯</span>
        <input
          className="flex-1 bg-transparent mono text-sm outline-none"
          style={{ color: 'var(--text)', caretColor: 'var(--green)' }}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="git status · github repos sandraschi · …"
          disabled={loading}
          autoFocus
        />
        <button onClick={() => send()} disabled={loading || !input.trim()}
          className="shrink-0 p-1 rounded transition-colors"
          style={{ color: input.trim() ? 'var(--green)' : 'var(--text-dim)' }}>
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
        </button>
      </div>
      </div>

      {/* Discovery: HTTP presets (fallback); MCP git_github_search_workflow = superior when sampling supported */}
      <aside
        className="flex flex-col shrink-0 w-full lg:w-[22rem] rounded p-3 gap-3"
        style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', maxHeight: 'min(70vh, 640px)' }}>
        <div className="flex items-start gap-2">
          <div className="h-8 w-8 rounded flex items-center justify-center shrink-0"
            style={{ background: 'var(--bg-3)', border: '1px solid var(--border)' }}>
            <Compass size={16} style={{ color: 'var(--cyan)' }} />
          </div>
          <div>
            <h2 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Discovery workflow</h2>
            <p className="text-[11px] leading-snug mt-0.5" style={{ color: 'var(--text-dim)' }}>
              <strong style={{ color: 'var(--text-muted)' }}>Best:</strong> MCP{' '}
              <span className="mono">git_github_search_workflow</span> in clients with full sampling
              (e.g. Antigravity) — LLM-planned steps. <strong style={{ color: 'var(--text-muted)' }}>Here:</strong>{' '}
              fixed <span className="mono">github_ops</span> presets for the web UI or when sampling
              is unavailable.
            </p>
          </div>
        </div>

        <label className="flex flex-col gap-1">
          <span className="text-[10px] uppercase tracking-wide" style={{ color: 'var(--text-dim)' }}>Preset</span>
          <select
            className="mono text-xs rounded px-2 py-1.5 outline-none"
            style={{ background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)' }}
            value={discPreset}
            onChange={e => setDiscPreset(e.target.value)}
            disabled={discLoading}>
            {DISCOVERY_PRESETS.map(p => (
              <option key={p.id} value={p.id}>{p.title}</option>
            ))}
          </select>
        </label>
        {presetMeta && (
          <p className="text-[11px] leading-snug -mt-1" style={{ color: 'var(--text-muted)' }}>{presetMeta.blurb}</p>
        )}

        <div className="grid grid-cols-2 gap-2">
          {(discPreset === 'org_snapshot' || discPreset === 'topic_hunt' || discPreset === 'code_sweep' || discPreset === 'repo_deep_dive') && (
            <label className="flex flex-col gap-0.5 col-span-2">
              <span className="text-[10px] mono" style={{ color: 'var(--text-dim)' }}>owner</span>
              <input
                className="mono text-xs rounded px-2 py-1 outline-none"
                style={{ background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--cyan)' }}
                value={discOwner}
                onChange={e => setDiscOwner(e.target.value)}
                placeholder="user or org"
                disabled={discLoading}
              />
            </label>
          )}
          {discPreset === 'repo_deep_dive' && (
            <label className="flex flex-col gap-0.5 col-span-2">
              <span className="text-[10px] mono" style={{ color: 'var(--text-dim)' }}>repo</span>
              <input
                className="mono text-xs rounded px-2 py-1 outline-none"
                style={{ background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--cyan)' }}
                value={discRepo}
                onChange={e => setDiscRepo(e.target.value)}
                placeholder="name"
                disabled={discLoading}
              />
            </label>
          )}
          {(discPreset === 'topic_hunt') && (
            <label className="flex flex-col gap-0.5 col-span-2">
              <span className="text-[10px] mono" style={{ color: 'var(--text-dim)' }}>topic</span>
              <input
                className="mono text-xs rounded px-2 py-1 outline-none"
                style={{ background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--cyan)' }}
                value={discTopic}
                onChange={e => setDiscTopic(e.target.value)}
                placeholder="e.g. mcp"
                disabled={discLoading}
              />
            </label>
          )}
          {(discPreset === 'topic_hunt') && (
            <label className="flex flex-col gap-0.5 col-span-2">
              <span className="text-[10px] mono" style={{ color: 'var(--text-dim)' }}>query (optional)</span>
              <input
                className="mono text-xs rounded px-2 py-1 outline-none"
                style={{ background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--cyan)' }}
                value={discQuery}
                onChange={e => setDiscQuery(e.target.value)}
                placeholder="extra search text"
                disabled={discLoading}
              />
            </label>
          )}
          {(discPreset === 'code_sweep') && (
            <label className="flex flex-col gap-0.5 col-span-2">
              <span className="text-[10px] mono" style={{ color: 'var(--text-dim)' }}>query</span>
              <input
                className="mono text-xs rounded px-2 py-1 outline-none"
                style={{ background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--cyan)' }}
                value={discQuery}
                onChange={e => setDiscQuery(e.target.value)}
                placeholder="code needle (optional if extension set)"
                disabled={discLoading}
              />
            </label>
          )}
          {(discPreset === 'code_sweep') && (
            <label className="flex flex-col gap-0.5 col-span-2">
              <span className="text-[10px] mono" style={{ color: 'var(--text-dim)' }}>extension</span>
              <input
                className="mono text-xs rounded px-2 py-1 outline-none"
                style={{ background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--cyan)' }}
                value={discExt}
                onChange={e => setDiscExt(e.target.value)}
                placeholder="e.g. bak"
                disabled={discLoading}
              />
            </label>
          )}
          {(discPreset === 'global_search') && (
            <label className="flex flex-col gap-0.5 col-span-2">
              <span className="text-[10px] mono" style={{ color: 'var(--text-dim)' }}>query</span>
              <input
                className="mono text-xs rounded px-2 py-1 outline-none"
                style={{ background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--cyan)' }}
                value={discQuery}
                onChange={e => setDiscQuery(e.target.value)}
                placeholder="mcp language:python"
                disabled={discLoading}
              />
            </label>
          )}
          <label className="flex flex-col gap-0.5 col-span-2">
            <span className="text-[10px] mono" style={{ color: 'var(--text-dim)' }}>limit</span>
            <input
              type="number"
              min={1}
              max={100}
              className="mono text-xs rounded px-2 py-1 outline-none w-full"
              style={{ background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)' }}
              value={discLimit}
              onChange={e => setDiscLimit(e.target.value)}
              disabled={discLoading}
            />
          </label>
        </div>

        <button
          type="button"
          onClick={runDiscovery}
          disabled={discLoading}
          className="mono text-xs font-medium py-2 rounded transition-opacity"
          style={{
            background: 'rgba(34,197,94,0.15)',
            border: '1px solid rgba(34,197,94,0.35)',
            color: 'var(--green)',
            opacity: discLoading ? 0.6 : 1,
          }}>
          {discLoading ? (
            <span className="inline-flex items-center justify-center gap-2">
              <Loader2 size={14} className="animate-spin" /> Running…
            </span>
          ) : (
            'Run discovery workflow'
          )}
        </button>

        {discResult && (
          <div className="flex flex-col gap-1 flex-1 min-h-0">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase tracking-wide" style={{ color: 'var(--text-dim)' }}>Result</span>
              <button
                type="button"
                onClick={copyDiscovery}
                className="flex items-center gap-1 mono text-[10px] px-1.5 py-0.5 rounded"
                style={{ border: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                {discCopied ? <Check size={12} style={{ color: 'var(--green)' }} /> : <Copy size={12} />}
                {discCopied ? 'Copied' : 'Copy JSON'}
              </button>
            </div>
            <pre
              className="mono text-[10px] leading-relaxed rounded p-2 flex-1 overflow-auto whitespace-pre-wrap break-all"
              style={{ background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)', maxHeight: 220 }}>
              {discResult}
            </pre>
          </div>
        )}
      </aside>
      </div>
    </div>
  );
}
