import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // bind all interfaces so the app is reachable from Windows when run in WSL
    proxy: {
      '/api': 'http://127.0.0.1:5001',
    },
  },
})
