import { useCallback, useEffect, useState } from 'react';

export type Capabilities = {
  status: string;
  server?: { name: string; version: string; fastmcp?: string };
  tool_surface?: {
    total: number;
    portmanteau_count: number;
    atomic_count: number;
    portmanteau_tools?: string[];
  };
  features?: Record<string, boolean>;
};

export function useCapabilities() {
  const [caps, setCaps] = useState<Capabilities | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const r = await fetch('/api/capabilities');
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setCaps((await r.json()) as Capabilities);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'capabilities failed');
      setCaps(null);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { caps, error, reload };
}
