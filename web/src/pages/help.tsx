export function HelpPage() {
  return (
    <div className="max-w-3xl space-y-4 text-sm text-muted-foreground">
      <h2 className="text-lg font-semibold text-foreground">Help</h2>
      <section className="rounded-lg border border-border bg-card/40 p-4 space-y-2">
        <h3 className="font-medium text-foreground">Quick start</h3>
        <ol className="list-decimal list-inside space-y-1">
          <li>
            Run <code className="text-gh-green">start.bat</code> or{' '}
            <code className="text-gh-green">mcp-central-docs\starts\git-github-mcp-start.bat</code> — frontend{' '}
            <strong>10703</strong>, backend <strong>10702</strong>.
          </li>
          <li>
            Open <strong>Breakfast</strong> for the full fleet maintainer suite (<code>fleet_ops full_suite</code>).
          </li>
          <li>
            Use <strong>Tools</strong> for MCP inspector; <strong>Logs</strong> for API/git activity ring buffer.
          </li>
          <li>
            Schedule daily digest: <code className="text-xs">scripts\install_morning_task.ps1</code>
          </li>
        </ol>
      </section>
      <section className="rounded-lg border border-border bg-card/40 p-4 space-y-2">
        <h3 className="font-medium text-foreground">HTTP endpoints</h3>
        <ul className="font-mono text-xs space-y-1">
          <li>GET /health</li>
          <li>GET /api/capabilities</li>
          <li>GET /api/tools</li>
          <li>GET /api/logs</li>
          <li>POST /api/fleet-suite</li>
          <li>POST /api/git · POST /api/github</li>
          <li>MCP HTTP /mcp</li>
        </ul>
      </section>
    </div>
  );
}
