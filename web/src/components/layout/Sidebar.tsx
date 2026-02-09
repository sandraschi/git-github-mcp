import { motion } from 'framer-motion'
import { GitBranch, Github, FileText, GitPullRequest, Terminal, ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { useState } from 'react'

interface SidebarProps {
  currentPage: string
  onNavigate: (page: string) => void
}

const menuItems = [
  { id: 'dashboard', label: 'Dashboard', icon: GitBranch },
  { id: 'repos', label: 'Repos', icon: Github },
  { id: 'glama', label: 'Glama', icon: Search },
  { id: 'issues', label: 'Issues', icon: FileText },
  { id: 'prs', label: 'Pull Requests', icon: GitPullRequest },
  { id: 'tools', label: 'Tool Runner', icon: Terminal },
]

export function Sidebar({ currentPage, onNavigate }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <motion.div
      animate={{ width: collapsed ? 72 : 220 }}
      className="h-screen bg-[#12121a] border-r border-[#1e1e2e] flex flex-col z-20 relative"
    >
      <div className="h-14 flex items-center px-4 border-b border-[#1e1e2e] shrink-0">
        <div className="flex items-center gap-3 overflow-hidden whitespace-nowrap">
          <GitBranch className="w-6 h-6 text-indigo-400 shrink-0" />
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="font-semibold text-sm bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-violet-500"
            >
              Git GitHub Hub
            </motion.span>
          )}
        </div>
      </div>

      <nav className="flex-1 py-4 flex flex-col gap-1 px-4">
        {menuItems.map((item) => {
          const isActive = currentPage === item.id
          const Icon = item.icon
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`
                relative flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
                ${isActive
                  ? 'bg-indigo-500/15 text-indigo-200 border border-indigo-500/30'
                  : 'text-slate-500 hover:bg-slate-800/50 hover:text-slate-200 border border-transparent'
                }
              `}
            >
              <Icon className="w-5 h-5 shrink-0" />
              {!collapsed && <span className="text-sm font-medium">{item.label}</span>}
              {collapsed && isActive && (
                <div className="absolute left-full ml-3 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-xs text-white whitespace-nowrap z-50 shadow-lg">
                  {item.label}
                </div>
              )}
            </button>
          )
        })}
      </nav>

      <button
        onClick={() => setCollapsed(!collapsed)}
        className="h-12 border-t border-[#1e1e2e] flex items-center justify-center text-slate-500 hover:text-slate-200 hover:bg-slate-800/50 transition-colors w-full shrink-0"
        title={collapsed ? 'Expand' : 'Collapse'}
      >
        {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
      </button>
    </motion.div>
  )
}
