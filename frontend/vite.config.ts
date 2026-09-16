import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': process.env.API_PROXY_TARGET ?? 'http://localhost:8000',
    },
    // Docker Desktop on Windows doesn't reliably forward filesystem change
    // events across the VM boundary for bind-mounted volumes, so chokidar's
    // native watcher silently misses edits. Polling is the standard fix.
    watch: {
      usePolling: true,
      interval: 300,
    },
  },
})
