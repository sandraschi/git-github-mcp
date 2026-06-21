import { useEffect, useState } from 'react';
import { ExternalLink } from 'lucide-react';
import { API_BASE } from '../lib/api';

type FleetApp = {
  id: string;
  name: string;
  description: string;
  port: number;
  category: string;
  url: string | null;
};

export function AppsPage() {
  const [apps, setApps] = useState<FleetApp[]>([]);
  const [fleetTotal, setFleetTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(API_BASE + '/api/apps')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((j) => {
        setApps((j.apps as FleetApp[]) ?? []);
        setFleetTotal(j.fleet_total ?? 0);
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'load failed'));
  }, []);

  return (
    <div>
      <p className="text-sm text-muted-foreground mb-4">
        {fleetTotal} repos in fleet registry · {apps.length} with webapp ports (from registry)
      </p>
      {error && <p className="text-sm text-red-400 mb-4">{error}</p>}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {apps.map((app) => (
          <a
            key={app.id}
            href={app.url ?? '#'}
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-border bg-card/40 p-4 hover:border-gh-green/30 hover:bg-white/[0.02] transition-colors"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium text-sm">{app.name}</span>
              <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
            </div>
            <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{app.description}</p>
            <p className="text-[10px] font-mono text-gh-green mt-2">:{app.port}</p>
          </a>
        ))}
      </div>
    </div>
  );
}
