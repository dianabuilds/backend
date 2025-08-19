import { defineConfig, type ProxyOptions } from 'vite'
import react from '@vitejs/plugin-react'

const apiPrefixes = [
  'auth',
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
  'media', // upload endpoint (cover/images)
]

const proxy = apiPrefixes.reduce<Record<string, ProxyOptions>>((acc, prefix) => {
  acc[`/${prefix}`] = {
    target: 'http://localhost:8000',
    changeOrigin: true,
    ...(prefix === 'notifications' ? { ws: true } : {}),
  }
  return acc
}, {})

// Точечные админские API (не перехватываем корневой /admin, чтобы SPA работала)
proxy['/admin/echo'] = { target: 'http://localhost:8000', changeOrigin: true }
proxy['/admin/navigation'] = { target: 'http://localhost:8000', changeOrigin: true }
proxy['/admin/users'] = { target: 'http://localhost:8000', changeOrigin: true }
proxy['/admin/menu'] = { target: 'http://localhost:8000', changeOrigin: true }
proxy['/admin/dashboard'] = { target: 'http://localhost:8000', changeOrigin: true }
proxy['/admin/cache'] = { target: 'http://localhost:8000', changeOrigin: true }
proxy['/admin/ratelimit'] = { target: 'http://localhost:8000', changeOrigin: true }
proxy['/admin/restrictions'] = { target: 'http://localhost:8000', changeOrigin: true }
proxy['/admin/audit'] = { target: 'http://localhost:8000', changeOrigin: true }
proxy['/admin/metrics'] = { target: 'http://localhost:8000', changeOrigin: true }
proxy['/admin/notifications'] = { target: 'http://localhost:8000', changeOrigin: true }
proxy['/admin/quests'] = {
  target: 'http://localhost:8000',
  changeOrigin: true,
  bypass(req) {
    const accept = req.headers['accept'] || '';
    if (typeof accept === 'string' && accept.includes('text/html')) {
      return '/admin/index.html';
    }
  },
}

proxy['/admin/tags'] = {
  target: 'http://localhost:8000',
  changeOrigin: true,
  bypass(req) {
    const accept = req.headers['accept'] || '';
    if (typeof accept === 'string' && accept.includes('text/html')) {
      return '/admin/index.html';
    }
  },
}
proxy['/admin/transitions'] = {
  target: 'http://localhost:8000',
  changeOrigin: true,
  bypass(req) {
    const accept = req.headers['accept'] || '';
    // Для навигации по SPA возвращаем индекс, а для JSON-запросов проксируем на backend
    if (typeof accept === 'string' && accept.includes('text/html')) {
      return '/admin/index.html';
    }
  },
}
proxy['/admin/traces'] = {
  target: 'http://localhost:8000',
  changeOrigin: true,
  bypass(req) {
    const accept = req.headers['accept'] || '';
    if (typeof accept === 'string' && accept.includes('text/html')) {
      return '/admin/index.html';
    }
  },
}
proxy['/admin/flags'] = { target: 'http://localhost:8000', changeOrigin: true }
proxy['/admin/nodes'] = { target: 'http://localhost:8000', changeOrigin: true }
proxy['/admin/achievements'] = { target: 'http://localhost:8000', changeOrigin: true }
proxy['/admin/moderation'] = { target: 'http://localhost:8000', changeOrigin: true }

// https://vite.dev/config/
export default defineConfig({
  base: '/admin/',
  plugins: [
    react(),
  ],
  server: {
    port: 5173,
    strictPort: false,
    open: '/admin/',
    proxy,
  },
})
