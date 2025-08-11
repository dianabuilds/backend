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

// https://vite.dev/config/
export default defineConfig({
  base: '/admin/',
  plugins: [
    react(),
    // Редиректим корень "/" на "/admin/" в dev, чтобы не попадать на пустую страницу
    {
      name: 'root-redirect-to-admin',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          const request = req as unknown as { url?: string; headers?: Record<string, string | string[] | undefined> }
          const url = request.url ?? ''
          const acceptHeader = request.headers?.['accept']
          const accept = (Array.isArray(acceptHeader) ? acceptHeader[0] : acceptHeader) ?? ''
          if (url === '/' && accept.includes('text/html')) {
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
