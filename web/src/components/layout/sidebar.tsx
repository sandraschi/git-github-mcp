"use client";

import {
  Activity,
  ChevronLeft,
  ChevronRight,
  Coffee,
  GitBranch,
  GitCommit,
  Github,
  HelpCircle,
  Inbox,
  LayoutDashboard,
  MessageSquare,
  Radar,
  Settings,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();
  const path = location.pathname;

  const navItems = [
    { label: "Dashboard", icon: LayoutDashboard, href: "/" },
    { label: "Tools", icon: GitBranch, href: "/tools" },
    { label: "Apps", icon: LayoutDashboard, href: "/apps" },
    { label: "Repositories", icon: GitBranch, href: "/repos" },
    { label: "Commits", icon: GitCommit, href: "/commits" },
    { label: "PRs & Issues", icon: Inbox, href: "/inbox" },
    { label: "Breakfast", icon: Coffee, href: "/breakfast" },
    { label: "CI Monitor", icon: Radar, href: "/ci" },
    { label: "Chat", icon: MessageSquare, href: "/chat" },
    { label: "Logs", icon: Activity, href: "/logs" },
    { label: "Help", icon: HelpCircle, href: "/help" },
    { label: "Settings", icon: Settings, href: "/settings" },
  ];

  return (
    <div
      className={cn(
        "flex flex-col border-r border-slate-800 bg-slate-950 text-slate-300 transition-all duration-300",
        collapsed ? "w-16" : "w-64",
      )}
    >
      <div className="flex h-16 items-center border-b border-slate-800 px-4">
        <div className="flex w-full items-center justify-between">
          {!collapsed && (
            <div className="flex items-center gap-2 font-semibold text-slate-100">
              <Github className="h-6 w-6" />
              <span>GitHub MCP</span>
            </div>
          )}
          {collapsed && <Github className="h-6 w-6 mx-auto" />}
          <button
            type="button"
            onClick={onToggle}
            className={cn(
              "rounded p-1 hover:bg-slate-800 text-slate-400 hover:text-slate-100 transition-colors",
              collapsed
                ? "absolute -right-3 top-6 bg-slate-900 border border-slate-700 rounded-full w-6 h-6 flex items-center justify-center p-0"
                : "",
            )}
          >
            {collapsed ? (
              <ChevronRight className="h-3 w-3" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => {
          const isActive = path === item.href;
          return (
            <Link
              key={item.href}
              to={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-600/10 text-blue-400"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-100",
                collapsed && "justify-center px-2",
              )}
              title={collapsed ? item.label : undefined}
            >
              <item.icon className="h-5 w-5" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-800 p-4">
        {!collapsed && <div className="text-xs text-slate-500">v0.5.0</div>}
      </div>
    </div>
  );
}
