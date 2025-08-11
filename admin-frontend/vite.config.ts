import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/users': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/nodes': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/moderation': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/transitions': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/navigation': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/notifications': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
      '/quests': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/traces': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/achievements': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/payments': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
