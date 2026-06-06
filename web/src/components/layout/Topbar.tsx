import { Link } from 'react-router-dom';
import { Activity, HelpCircle } from 'lucide-react';
import { useCapabilities } from '@/hooks/use-capabilities';

export function Topbar({ label }: { label: string }) {
  const { caps, error } = useCapabilities();
  const version = caps?.server?.version ?? '—';
  const toolCount = caps?.tool_surface?.total ?? 0;

  return (
    <header className="relative z-20 flex h-14 shrink-0 items-center justify-between border-b border-border bg-card/40 backdrop-blur-md px-6">
      <h1 className="text-sm font-semibold tracking-tight text-foreground">{label}</h1>
      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span className="hidden sm:inline font-mono">
          {error ? 'capabilities offline' : `v${version} · ${toolCount} tools`}
        </span>
        {caps?.features?.local_llm && (
          <span className="px-2 py-0.5 rounded border border-gh-green/30 text-gh-green">Ollama/LM Studio</span>
        )}
        <Link to="/help" className="p-1.5 rounded hover:bg-white/5 hover:text-foreground" title="Help">
          <HelpCircle className="h-4 w-4" />
        </Link>
        <Link to="/logs" className="p-1.5 rounded hover:bg-white/5 hover:text-foreground" title="Logs">
          <Activity className="h-4 w-4" />
        </Link>
      </div>
    </header>
  );
}
