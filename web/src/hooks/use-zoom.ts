import { useCallback, useEffect, useRef } from "react";

const ZOOM_LEVELS = [0.8, 1.0, 1.25, 1.5, 2.0, 3.0];

export function useZoom() {
  const zoomIndex = useRef(1);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("tauri-zoom");
      if (saved) {
        const idx = ZOOM_LEVELS.indexOf(parseFloat(saved));
        if (idx >= 0) zoomIndex.current = idx;
      }
    } catch {
      /* ignore */
    }
  }, []);

  const applyZoom = useCallback(async (level: number) => {
    localStorage.setItem("tauri-zoom", String(level));
    try {
      const { getCurrentWindow } = await import("@tauri-apps/api/window");
      const win = getCurrentWindow() as unknown as {
        setZoom?: (level: number) => Promise<void>;
      };
      if (typeof win.setZoom === "function") {
        await win.setZoom(level);
        return;
      }
    } catch {
      /* not in Tauri — fall through to CSS zoom */
    }
    document.documentElement.style.zoom = String(level);
  }, []);

  useEffect(() => {
    const handler = (e: WheelEvent) => {
      if (!e.ctrlKey) return;
      e.preventDefault();
      const next =
        e.deltaY < 0
          ? Math.min(zoomIndex.current + 1, ZOOM_LEVELS.length - 1)
          : Math.max(zoomIndex.current - 1, 0);
      if (next !== zoomIndex.current) {
        zoomIndex.current = next;
        applyZoom(ZOOM_LEVELS[next]);
      }
    };
    window.addEventListener("wheel", handler, { passive: false });
    const saved = localStorage.getItem("tauri-zoom");
    if (saved) applyZoom(parseFloat(saved));
    return () => window.removeEventListener("wheel", handler);
  }, [applyZoom]);
}
