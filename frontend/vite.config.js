import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const BACKEND_PORT = process.env.BACKEND_PORT || '8001';
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    tailwindcss(),
    react()
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: BACKEND_URL,
        changeOrigin: true
      },
      '/videos': {
        target: BACKEND_URL,
        changeOrigin: true
      },
      '/snapshots': {
        target: BACKEND_URL,
        changeOrigin: true
      },
      '/evidence': {
        target: BACKEND_URL,
        changeOrigin: true
      }
    }
  }
})
