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
proxy['/admin/quests'] = { target: 'http://localhost:8000', changeOrigin: true }

// https://vite.dev/config/
export default defineConfig({
  base: '/admin/',
  plugins: [
    react(),
    // SPA fallback в dev:
    // - любые HTML-запросы на /admin/* (кроме ассетов) отправляем на /admin/
    // - XHR (application/json и т.п.) продолжат проксироваться на бэкенд
    {
      name: 'admin-spa-fallback',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          const request = req as unknown as { url?: string; headers?: Record<string, string | string[] | undefined>; method?: string }
          const url = request.url ?? ''
          const method = (request.method || 'GET').toUpperCase()
          const acceptHeader = request.headers?.['accept']
          const accept = (Array.isArray(acceptHeader) ? acceptHeader[0] : acceptHeader) ?? ''

          // Только для GET HTML-запросов на вложенные пути /admin/*
          const isHtml = accept.includes('text/html')
          const isAdminNested = url.startsWith('/admin/') // важно: со слешом после admin
          const isAdminRoot = url === '/admin' || url === '/admin/'
          const isAsset = url.startsWith('/admin/assets')

          // Явно правим /admin -> /admin/, чтобы не видеть предупреждение Vite о base URL
          if (method === 'GET' && isHtml && url === '/admin') {
            res.statusCode = 302
            res.setHeader('Location', '/admin/')
            res.end()
            return
          }

          if (method === 'GET' && isHtml && isAdminNested && !isAsset && !isAdminRoot) {
            // Перенаправляем только вложенные маршруты на корневой SPA
            res.statusCode = 302
            res.setHeader('Location', '/admin/')
            res.end()
            return
          }
          next()
        })
      },
    },
  ],
  server: {
    port: 5173,
    strictPort: false,
    open: '/admin/',
    proxy,
  },
})
