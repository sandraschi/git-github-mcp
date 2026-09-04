import { useState } from "react";
import { useLogger } from "@/context/logger-context";

export function LoggerPanel() {
  const { lines } = useLogger();
  const [open, setOpen] = useState(false);

  return (
    <div className="border-t border-border bg-zinc-950 shrink-0">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-2 text-xs text-zinc-400 hover:text-zinc-100 hover:bg-white/5"
      >
        <span>Event log ({lines.length})</span>
        <span>{open ? "▼" : "▲"}</span>
      </button>
      {open && (
        <pre className="max-h-40 overflow-auto px-4 pb-3 text-[11px] text-zinc-400 font-mono whitespace-pre-wrap bg-black/20 border-t border-white/5">
          {lines.length === 0 ? "No events yet." : lines.join("\n")}
        </pre>
      )}
    </div>
  );
}
