import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  GitCommit, GitPullRequest, CircleDot,
  MessageSquare, Settings, ChevronRight, Terminal,
  LayoutDashboard, BookOpen, GraduationCap
} from 'lucide-react';

const NAV = [
  { to: '/',        icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/repos',   icon: BookOpen,         label: 'Repos' },
  { to: '/commits', icon: GitCommit,        label: 'Commits' },
  { to: '/issues',  icon: CircleDot,        label: 'Issues' },
  { to: '/prs',     icon: GitPullRequest,   label: 'Pull Requests' },
  { to: '/chat',    icon: MessageSquare,    label: 'Command' },
  { to: '/lectures',icon: GraduationCap,    label: 'Lectures' },
  { to: '/settings',icon: Settings,         label: 'Settings' },
];

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-full" style={{ background: 'var(--bg)' }}>
      {/* Sidebar */}
      <aside
        className="flex flex-col transition-all duration-200 shrink-0"
        style={{
          width: collapsed ? 52 : 200,
          background: 'var(--bg-2)',
          borderRight: '1px solid var(--border)',
        }}
      >
        {/* Logo */}
        <div
          className="flex items-center gap-2 px-3 py-4 cursor-pointer select-none"
          onClick={() => setCollapsed(c => !c)}
          style={{ borderBottom: '1px solid var(--border)' }}
        >
          <div
            className="shrink-0 flex items-center justify-center rounded"
            style={{
              width: 28, height: 28,
              background: 'var(--green-glow)',
              border: '1px solid var(--green-dim)',
            }}
          >
            <Terminal size={14} style={{ color: 'var(--green)' }} />
          </div>
          {!collapsed && (
            <span className="text-sm font-bold tracking-tight truncate" style={{ color: 'var(--green)', fontFamily: 'var(--font-mono)' }}>
              git·hub·mcp
            </span>
          )}
          <ChevronRight
            size={12}
            className="ml-auto shrink-0 transition-transform duration-200"
            style={{
              color: 'var(--text-dim)',
              transform: collapsed ? 'rotate(0deg)' : 'rotate(180deg)',
            }}
          />
        </div>

        {/* Nav */}
        <nav className="flex-1 py-2 flex flex-col gap-0.5 px-1.5">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-2 py-2 rounded text-sm transition-all duration-150 ${
                  isActive
                    ? 'text-white'
                    : 'hover:text-white'
                }`
              }
              style={({ isActive }) => ({
                background: isActive ? 'var(--bg-3)' : 'transparent',
                color: isActive ? 'var(--text)' : 'var(--text-muted)',
                border: isActive ? '1px solid var(--border)' : '1px solid transparent',
              })}
            >
              {({ isActive }) => (
                <>
                  <Icon size={15} style={{ color: isActive ? 'var(--green)' : undefined, flexShrink: 0 }} className="shrink-0" />
                  {!collapsed && <span className="truncate">{label}</span>}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Version tag */}
        {!collapsed && (
          <div className="px-3 py-3" style={{ borderTop: '1px solid var(--border)' }}>
            <span className="mono text-xs" style={{ color: 'var(--text-dim)' }}>v0.2.0 · FastMCP 3.0</span>
          </div>
        )}
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto p-6 fade-up">
        {children}
      </main>
    </div>
  );
}
