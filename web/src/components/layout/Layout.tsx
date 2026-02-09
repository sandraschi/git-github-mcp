import { type ReactNode } from 'react'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'

interface LayoutProps {
  children: ReactNode
  currentPage: string
  onNavigate: (page: string) => void
  onShowLogger: () => void
  onShowHelp: () => void
}

export function Layout({ children, currentPage, onNavigate, onShowLogger, onShowHelp }: LayoutProps) {
  return (
    <div className="flex h-screen bg-[#0a0a0f] text-slate-200 overflow-hidden font-mono selection:bg-indigo-500/30">
      <Sidebar currentPage={currentPage} onNavigate={onNavigate} />
      <div className="flex-1 flex flex-col min-w-0 transition-all duration-300">
        <Topbar title={currentPage} onShowLogger={onShowLogger} onShowHelp={onShowHelp} />
        <main className="flex-1 overflow-y-auto overflow-x-hidden p-6 bg-mesh">
          <div className="max-w-6xl mx-auto space-y-6">{children}</div>
        </main>
      </div>
    </div>
  )
}
