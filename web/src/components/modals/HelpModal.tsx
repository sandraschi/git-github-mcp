import { X } from 'lucide-react'

interface HelpModalProps {
  isOpen: boolean
  onClose: () => void
}

const helpContent = `
# Git GitHub Hub

Simple UI for Git and GitHub. Requires:
- **gh CLI** authenticated (\`gh auth login\`)
- **Git** installed

## Pages
- **Dashboard**: Overview
- **Repos**: Your GitHub repos
- **Issues**: List/create issues
- **PRs**: List/create pull requests
- **Tool Runner**: Run git_ops and github_ops directly

## Shortcuts
- \`?\` - Help
- \`Ctrl/Cmd + /\` - Logger
`.trim()

export function HelpModal({ isOpen, onClose }: HelpModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-[#12121a] border border-[#1e1e2e] rounded-xl shadow-2xl max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-200">Help</h2>
          <button onClick={onClose} className="p-2 rounded-lg text-slate-500 hover:text-slate-200 hover:bg-slate-800/50">
            <X size={20} />
          </button>
        </div>
        <pre className="text-sm text-slate-400 whitespace-pre-wrap font-mono">{helpContent}</pre>
      </div>
    </div>
  )
}
