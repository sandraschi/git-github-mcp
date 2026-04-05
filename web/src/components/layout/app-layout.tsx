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
    <div className="flex h-screen bg-background text-foreground selection:bg-gh-green/30">
      {/* Sidebar */}
      <aside
        className={`flex flex-col transition-all duration-300 ease-in-out border-r border-border bg-card/50 backdrop-blur-xl z-20 ${
          collapsed ? 'w-16' : 'w-64'
        }`}
      >
        {/* Logo Section */}
        <div 
          className="h-16 flex items-center px-4 border-b border-border cursor-pointer hover:bg-white/5 transition-colors group"
          onClick={() => setCollapsed(!collapsed)}
        >
          <div className="w-8 h-8 rounded-lg bg-gh-green/10 border border-gh-green/20 flex items-center justify-center group-hover:border-gh-green/40 transition-all">
            <Terminal className="w-4 h-4 text-gh-green shadow-[0_0_10px_rgba(34,197,94,0.3)]" />
          </div>
          {!collapsed && (
            <div className="ml-3 flex flex-col overflow-hidden">
              <span className="font-heading font-black text-sm tracking-tighter text-gh-green uppercase truncate">
                git·hub·mcp
              </span>
              <span className="text-[10px] text-muted-foreground font-mono leading-none">v1.20.0 · ARC-AGI</span>
            </div>
          )}
          <ChevronRight 
            className={`ml-auto w-4 h-4 text-muted-foreground transition-transform duration-300 ${
              collapsed ? '' : 'rotate-180'
            }`} 
          />
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto overflow-x-hidden custom-scrollbar">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center h-10 px-3 rounded-md transition-all duration-200 group relative ${
                  isActive 
                    ? 'bg-gh-green/10 text-gh-green border border-gh-green/20' 
                    : 'text-muted-foreground hover:bg-white/5 hover:text-foreground border border-transparent'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0 transition-transform group-hover:scale-110" />
              {!collapsed && (
                <span className="ml-3 text-sm font-medium truncate">{label}</span>
              )}
              {collapsed && (
                <div className="absolute left-14 bg-popover text-popover-foreground px-2 py-1 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity border border-border shadow-xl z-50">
                  {label}
                </div>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-border bg-black/20">
          {!collapsed ? (
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-gh-green animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">System Online</span>
              </div>
              <span className="text-[9px] font-mono text-muted-foreground/60">Node: Vienna·Goliath v1.20</span>
            </div>
          ) : (
            <div className="flex justify-center">
              <div className="w-2 h-2 rounded-full bg-gh-green animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
            </div>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden relative">
        {/* Topbar background glow */}
        <div className="absolute top-0 left-0 w-full h-64 bg-gradient-to-b from-gh-green/5 to-transparent pointer-events-none" />
        
        {/* Page Content */}
        <div className="flex-1 overflow-auto relative z-10 p-6 md:p-8 custom-scrollbar">
          <div className="max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
