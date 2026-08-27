import {
  BookOpen,
  ChevronRight,
  CircleDot,
  Coffee,
  GitCommit,
  GitPullRequest,
  GraduationCap,
  Grid3X3,
  HelpCircle,
  Inbox,
  LayoutDashboard,
  MessageSquare,
  ScrollText,
  Settings,
  Terminal,
  Wrench,
} from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Topbar } from "@/components/layout/topbar";
import { LoggerPanel } from "@/components/logger-panel";
import { useBackendHealth } from "@/hooks/use-backend-health";
import { useZoom } from "@/hooks/use-zoom";

const FLEET_NAV = [
  { to: "/", icon: LayoutDashboard, label: "Home" },
  { to: "/tools", icon: Wrench, label: "Tools" },
  { to: "/logs", icon: ScrollText, label: "Logs" },
  { to: "/apps", icon: Grid3X3, label: "Apps" },
  { to: "/help", icon: HelpCircle, label: "Help" },
] as const;

const DOMAIN_NAV = [
  { to: "/repos", icon: BookOpen, label: "Repos" },
  { to: "/commits", icon: GitCommit, label: "Commits" },
  { to: "/inbox", icon: Inbox, label: "PRs & Issues" },
  { to: "/breakfast", icon: Coffee, label: "Breakfast" },
  { to: "/issues", icon: CircleDot, label: "Issues" },
  { to: "/prs", icon: GitPullRequest, label: "Pull Requests" },
  { to: "/chat", icon: MessageSquare, label: "Command" },
  { to: "/lectures", icon: GraduationCap, label: "Lectures" },
  { to: "/settings", icon: Settings, label: "Settings" },
] as const;

const PAGE_LABELS: Record<string, string> = {
  "/": "Dashboard",
  "/tools": "MCP Tools",
  "/logs": "Event Logs",
  "/apps": "Fleet Apps",
  "/help": "Help",
  "/repos": "Repositories",
  "/commits": "Commits",
  "/inbox": "PRs & Issues",
  "/breakfast": "Breakfast Runner",
  "/issues": "Issues",
  "/prs": "Pull Requests",
  "/chat": "Command",
  "/lectures": "Lectures",
  "/settings": "Settings",
};

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const pageLabel = PAGE_LABELS[location.pathname] ?? "git-github-mcp";
  const backendOk = useBackendHealth();
  useZoom();

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center h-10 px-3 rounded-md transition-all duration-200 group relative ${
      isActive
        ? "bg-gh-green/10 text-gh-green border border-gh-green/20"
        : "text-muted-foreground hover:bg-white/5 hover:text-foreground border border-transparent"
    }`;

  return (
    <div className="flex h-screen bg-background text-foreground selection:bg-gh-green/30">
      <aside
        className={`flex flex-col transition-all duration-300 ease-in-out border-r border-border bg-card/50 backdrop-blur-xl z-20 ${
          collapsed ? "w-16" : "w-64"
        }`}
      >
        <button
          type="button"
          className="h-16 flex items-center px-4 border-b border-border cursor-pointer hover:bg-white/5 transition-colors group w-full text-left"
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
              <span className="text-[10px] text-muted-foreground font-mono leading-none">
                v0.5.0
              </span>
            </div>
          )}
          <ChevronRight
            className={`ml-auto w-4 h-4 text-muted-foreground transition-transform duration-300 ${
              collapsed ? "" : "rotate-180"
            }`}
          />
        </button>

        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto overflow-x-hidden custom-scrollbar">
          {!collapsed && (
            <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 px-3 mb-2">
              Fleet
            </div>
          )}
          {FLEET_NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={navLinkClass}
              title={label}
            >
              <Icon className="w-4 h-4 shrink-0 transition-transform group-hover:scale-110" />
              {!collapsed && (
                <span className="ml-3 text-sm font-medium truncate">
                  {label}
                </span>
              )}
            </NavLink>
          ))}
          {!collapsed && (
            <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 px-3 mt-4 mb-2">
              GitHub
            </div>
          )}
          {DOMAIN_NAV.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} className={navLinkClass} title={label}>
              <Icon className="w-4 h-4 shrink-0 transition-transform group-hover:scale-110" />
              {!collapsed && (
                <span className="ml-3 text-sm font-medium truncate">
                  {label}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-border bg-black/20">
          {!collapsed ? (
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <div
                  data-testid="backend-dot"
                  className={`w-2 h-2 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)] ${
                    backendOk === null
                      ? "bg-gray-500"
                      : backendOk
                        ? "bg-gh-green"
                        : "bg-red-500"
                  }`}
                />
                <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                  {backendOk === null
                    ? "Connecting..."
                    : backendOk
                      ? "Online"
                      : "Offline"}
                </span>
              </div>
              <span className="text-[9px] font-mono text-muted-foreground/60">
                :10713 / :10714
              </span>
              {backendOk === false && (
                <button
                  type="button"
                  onClick={async () => {
                    try {
                      const { invoke } = await import("@tauri-apps/api/core");
                      await invoke("start_backend");
                    } catch {
                      /* not in Tauri */
                    }
                  }}
                  className="mt-1 text-[10px] font-mono px-2 py-0.5 rounded bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
                >
                  Restart Backend
                </button>
              )}
            </div>
          ) : (
            <div className="flex justify-center">
              <div
                data-testid="backend-dot"
                className={`w-2 h-2 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)] ${
                  backendOk === null
                    ? "bg-gray-500"
                    : backendOk
                      ? "bg-gh-green"
                      : "bg-red-500"
                }`}
              />
            </div>
          )}
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0 relative">
        <div className="absolute top-0 left-0 w-full h-64 bg-gradient-to-b from-gh-green/5 to-transparent pointer-events-none" />
        <Topbar label={pageLabel} />
        <main className="flex-1 overflow-auto relative z-10 p-6 md:p-8 custom-scrollbar">
          <div className="max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
            <Outlet />
          </div>
        </main>
        <LoggerPanel />
      </div>
    </div>
  );
}
