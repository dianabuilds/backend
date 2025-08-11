import { defineConfig, type ProxyOptions } from 'vite'
import react from '@vitejs/plugin-react'

const apiPrefixes = [
  'auth',
  'admin',
  'users',
  'nodes',
  'tags',
  'moderation',
  'transitions',
  'navigation',
  'notifications',
  'quests',
  'traces',
  'achievements',
  'payments',
  'search',
]

const proxy = apiPrefixes.reduce<Record<string, ProxyOptions>>((acc, prefix) => {
  acc[`/${prefix}`] = {
    target: 'http://localhost:8000',
    changeOrigin: true,
    ...(prefix === 'notifications' ? { ws: true } : {}),
  }
  return acc
}, {})

// https://vite.dev/config/
export default defineConfig({
  base: '/admin/',
  plugins: [react()],
  server: {
    proxy,
  },
})
