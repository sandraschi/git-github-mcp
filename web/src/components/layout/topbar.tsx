import { Activity, HelpCircle, Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useBackendHealth } from "@/hooks/use-backend-health";
import { useCapabilities } from "@/hooks/use-capabilities";

// EXPERIMENTAL light mode (invert hack). Not fleet standard — see index.css.
// Toggling `.dark` off the root flips the invert filter; persisted so the
// choice survives reloads. Delete this + the CSS block to revert.
const THEME_KEY = "git-github-mcp-light-mode";

function useExperimentalTheme() {
  const [light, setLight] = useState(() => {
    try {
      return localStorage.getItem(THEME_KEY) === "1";
    } catch {
      return false;
    }
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", !light);
    try {
      localStorage.setItem(THEME_KEY, light ? "1" : "0");
    } catch {
      // ignore storage errors
    }
  }, [light]);

  return { light, toggle: () => setLight((v) => !v) };
}

export function Topbar({ label }: { label: string }) {
  const { caps, error } = useCapabilities();
  const backendOk = useBackendHealth();
  const { light, toggle } = useExperimentalTheme();
  const version = caps?.server?.version ?? "—";
  const toolCount = caps?.tool_surface?.total ?? 0;

  return (
    <header className="relative z-20 flex h-14 shrink-0 items-center justify-between border-b border-border bg-card/40 backdrop-blur-md px-6">
      <h1 className="text-sm font-semibold tracking-tight text-foreground">
        {label}
      </h1>
      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <button
          type="button"
          onClick={toggle}
          className="p-1.5 rounded hover:bg-white/5 hover:text-foreground"
          title={
            light
              ? "Switch to dark (experimental light mode)"
              : "Switch to light (experimental, ugly)"
          }
          aria-label="Toggle light mode (experimental)"
        >
          {light ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </button>
        <div
          data-testid="backend-dot"
          className={`w-2 h-2 rounded-full ${
            backendOk === null
              ? "bg-gray-500"
              : backendOk
                ? "bg-green-500"
                : "bg-red-500"
          } animate-pulse`}
          title={
            backendOk === null
              ? "Connecting..."
              : backendOk
                ? "Backend connected"
                : "Backend offline"
          }
        />
        <span className="hidden sm:inline font-mono">
          {error ? "capabilities offline" : `v${version} · ${toolCount} tools`}
        </span>
        {caps?.features?.local_llm && (
          <span className="px-2 py-0.5 rounded border border-gh-green/30 text-gh-green">
            Ollama/LM Studio
          </span>
        )}
        <Link
          to="/help"
          className="p-1.5 rounded hover:bg-white/5 hover:text-foreground"
          title="Help"
        >
          <HelpCircle className="h-4 w-4" />
        </Link>
        <Link
          to="/logs"
          className="p-1.5 rounded hover:bg-white/5 hover:text-foreground"
          title="Logs"
        >
          <Activity className="h-4 w-4" />
        </Link>
      </div>
    </header>
  );
}
