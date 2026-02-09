import { Terminal, HelpCircle } from 'lucide-react'

interface TopbarProps {
  title: string
  onShowLogger: () => void
  onShowHelp: () => void
}

export function Topbar({ title, onShowLogger, onShowHelp }: TopbarProps) {
  const pageTitle = title.charAt(0).toUpperCase() + title.slice(1)

  return (
    <header className="h-14 border-b border-[#1e1e2e] flex items-center justify-between px-6 bg-[#0a0a0f]/80 backdrop-blur sticky top-0 z-30">
      <h1 className="text-lg font-semibold text-slate-200">{pageTitle}</h1>
      <div className="flex items-center gap-2">
        <button
          onClick={onShowLogger}
          className="p-2 rounded-lg text-slate-500 hover:text-slate-200 hover:bg-slate-800/50 transition-colors"
          title="Logger (Ctrl/Cmd + /)"
        >
          <Terminal size={20} />
        </button>
        <button
          onClick={onShowHelp}
          className="p-2 rounded-lg text-slate-500 hover:text-slate-200 hover:bg-slate-800/50 transition-colors"
          title="Help (?)"
        >
          <HelpCircle size={20} />
        </button>
      </div>
    </header>
  )
}
