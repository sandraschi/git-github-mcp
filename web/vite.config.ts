import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Backend (FastAPI) runs on 10702
// Vite dev server runs on 10703, proxies /api → 10702
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    port: 10703,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:10702',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 10703,
  },
})
