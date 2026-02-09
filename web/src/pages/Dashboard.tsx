import { GitBranch, Github, FileText, GitPullRequest } from 'lucide-react'

export function Dashboard() {
  return (
    <div className="space-y-8">
      <div className="text-slate-400 text-sm">
        Git GitHub Hub - simpler UI for Git and GitHub. Use sidebar to navigate.
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { id: 'repos', label: 'Repos', icon: Github, desc: 'Your GitHub repositories' },
          { id: 'issues', label: 'Issues', icon: FileText, desc: 'List and create issues' },
          { id: 'prs', label: 'Pull Requests', icon: GitPullRequest, desc: 'List and create PRs' },
          { id: 'tools', label: 'Tool Runner', icon: GitBranch, desc: 'Run git_ops and github_ops' },
        ].map(({ id, label, icon: Icon, desc }) => (
          <div
            key={id}
            className="p-6 rounded-xl bg-[#12121a] border border-[#1e1e2e] hover:border-indigo-500/30 transition-colors"
          >
            <Icon className="w-8 h-8 text-indigo-400 mb-3" />
            <h3 className="font-semibold text-slate-200 mb-1">{label}</h3>
            <p className="text-sm text-slate-500">{desc}</p>
          </div>
        ))}
      </div>

      <div className="p-6 rounded-xl bg-[#12121a] border border-[#1e1e2e]">
        <h3 className="font-semibold text-slate-200 mb-2">Requirements</h3>
        <ul className="text-sm text-slate-400 space-y-1 list-disc list-inside">
          <li>gh CLI installed and authenticated (gh auth login)</li>
          <li>Git installed</li>
        </ul>
      </div>
    </div>
  )
}
