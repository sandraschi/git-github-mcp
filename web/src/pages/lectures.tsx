import { useMemo, useState } from 'react';
import { BookOpen, Search } from 'lucide-react';

type Lecture = {
  key: string;
  title: string;
  summary: string;
  commands: string[];
  pitfalls: string[];
};

const LECTURES: Lecture[] = [
  {
    key: 'rebase',
    title: 'Rebase',
    summary: 'Replay your branch commits on top of a new base to keep history linear.',
    commands: ['git fetch origin', 'git rebase origin/main', 'git rebase --continue', 'git rebase --abort'],
    pitfalls: ['Do not rebase shared branch history unless your team expects it.', 'Resolve conflicts carefully; test before force-push.'],
  },
  {
    key: 'merge-vs-rebase',
    title: 'Merge vs Rebase',
    summary: 'Merge preserves branch topology. Rebase rewrites ancestry for cleaner feature history.',
    commands: ['git merge main', 'git rebase main'],
    pitfalls: ['Rebase changes commit SHAs.', 'Merge commits can clutter history if overused on small branches.'],
  },
  {
    key: 'cherry-pick',
    title: 'Cherry-pick',
    summary: 'Copy specific commit(s) to another branch, ideal for backports/hotfixes.',
    commands: ['git cherry-pick <sha>', 'git cherry-pick --abort'],
    pitfalls: ['Can duplicate fixes if the same changes are merged later.', 'Watch for context drift and conflicts on older branches.'],
  },
  {
    key: 'revert-vs-reset',
    title: 'Revert vs Reset',
    summary: 'Revert creates a new commit that undoes changes; reset moves branch pointers.',
    commands: ['git revert <sha>', 'git reset --soft HEAD~1', 'git reset --hard <sha>'],
    pitfalls: ['Avoid hard reset on shared history.', 'Prefer revert for public branches.'],
  },
  {
    key: 'github-projects',
    title: 'GitHub Projects',
    summary: 'Track work at org/user level with project boards and custom fields.',
    commands: ['gh project list --owner @me', 'gh project view <number> --owner @me', 'gh project create --owner @me --title "<title>"'],
    pitfalls: ['Needs project scope: gh auth refresh -s project.', 'Project numbering is owner-scoped.'],
  },
  {
    key: 'github-packages',
    title: 'GitHub Packages',
    summary: 'Host packages in GitHub registries (container, npm, maven, etc.).',
    commands: ['gh api user/packages?package_type=container', 'gh api orgs/<org>/packages?package_type=npm'],
    pitfalls: ['Requires read:packages or write:packages scopes.', 'Org package deletes typically require admin permissions.'],
  },
  {
    key: 'gitingest',
    title: 'Gitingest (repo digest for LLMs)',
    summary: 'Turn a GitHub repo or folder into one prompt-friendly text dump (tree + files + token estimate). Replace hub→ingest in github.com.',
    commands: [
      'Open: https://gitingest.com/owner/repo',
      'MCP: github_ops(operation="gitingest_link", owner="…", repo="…", ref="main", subpath="src")',
      'CLI: pipx install gitingest — gitingest https://github.com/owner/repo --output -',
    ],
    pitfalls: [
      'Public repos only unless you configure a PAT in Gitingest/CLI.',
      'Does not replace llms.txt — curated manifests stay the stable fleet entry point.',
    ],
  },
];

export function Lectures() {
  const [query, setQuery] = useState('');
  const q = query.trim().toLowerCase();

  const filtered = useMemo(() => {
    if (!q) return LECTURES;
    return LECTURES.filter((l) =>
      `${l.key} ${l.title} ${l.summary} ${l.commands.join(' ')} ${l.pitfalls.join(' ')}`.toLowerCase().includes(q),
    );
  }, [q]);

  return (
    <div className="max-w-5xl space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Git/GitHub Lectures</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
          Instant lookup for concepts like <span className="mono">rebase</span>, projects, packages, and recovery patterns.
        </p>
      </div>

      <div className="flex items-center gap-2 px-3 py-2 rounded" style={{ background: 'var(--bg-2)', border: '1px solid var(--border)' }}>
        <Search size={14} style={{ color: 'var(--text-dim)' }} />
        <input
          className="flex-1 bg-transparent text-sm outline-none"
          style={{ color: 'var(--text)', caretColor: 'var(--green)' }}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder='Try: "rebase", "cherry", "packages", "project"'
        />
      </div>

      <div className="grid gap-3">
        {filtered.map((lecture) => (
          <article key={lecture.key} className="rounded p-4" style={{ background: 'var(--bg-2)', border: '1px solid var(--border)' }}>
            <div className="flex items-center gap-2 mb-2">
              <BookOpen size={14} style={{ color: 'var(--green)' }} />
              <h2 className="text-lg font-semibold">{lecture.title}</h2>
              <span className="mono text-xs ml-auto" style={{ color: 'var(--text-dim)' }}>{lecture.key}</span>
            </div>
            <p className="text-sm mb-3" style={{ color: 'var(--text-muted)' }}>{lecture.summary}</p>
            <div className="mb-3">
              <div className="text-xs font-semibold mb-1" style={{ color: 'var(--text-dim)' }}>Commands</div>
              <pre className="mono text-xs p-2 rounded whitespace-pre-wrap" style={{ background: 'var(--bg)', border: '1px solid var(--border)' }}>
                {lecture.commands.join('\n')}
              </pre>
            </div>
            <div>
              <div className="text-xs font-semibold mb-1" style={{ color: 'var(--text-dim)' }}>Pitfalls</div>
              <ul className="text-xs list-disc pl-5 space-y-1" style={{ color: 'var(--text-muted)' }}>
                {lecture.pitfalls.map((p) => (
                  <li key={p}>{p}</li>
                ))}
              </ul>
            </div>
          </article>
        ))}
        {filtered.length === 0 && (
          <div className="text-sm" style={{ color: 'var(--text-dim)' }}>
            No lecture match. Try a broader term like <span className="mono">rebase</span> or <span className="mono">packages</span>.
          </div>
        )}
      </div>
    </div>
  );
}
