import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Backend (FastAPI) runs on 10713
// Vite dev server runs on 10714, proxies /api → 10713
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  server: {
    port: 10714,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://localhost:10713",
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 10714,
  },
});
