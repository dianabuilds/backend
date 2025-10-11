import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

const MAIN_ENTRY = path.resolve(__dirname, 'src/main.tsx');
const PUBLIC_ENTRY = path.resolve(__dirname, 'src/public-entry.tsx');

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');
  const target = env.VITE_API_BASE || 'http://127.0.0.1:8000';

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@ui': path.resolve(__dirname, 'src/shared/ui'),
        '@icons': path.resolve(__dirname, 'src/shared/icons'),
        '@': path.resolve(__dirname, 'vendor/template/src'),
        '@constants': path.resolve(__dirname, 'vendor/template/src/constants'),
        '@utils': path.resolve(__dirname, 'vendor/template/src/utils'),
        '@shared': path.resolve(__dirname, 'src/shared'),
      },
    },
    server: {
      host: '127.0.0.1',
      port: 5173,
      strictPort: true,
      fs: { strict: true },
      proxy: {
        '/v1': {
          target,
          changeOrigin: true,
          secure: false,
        },
        '/api': {
          target,
          changeOrigin: true,
          secure: false,
        },
      },
    },
    optimizeDeps: {
      entries: ['src/main.tsx', 'src/public-entry.tsx'],
    },
    build: {
      chunkSizeWarningLimit: 1300,
      outDir: 'dist/client',
      manifest: true,
      rollupOptions: {
        input: {
          main: MAIN_ENTRY,
          public: PUBLIC_ENTRY,
        },
        output: {
          manualChunks(id) {
            const normalized = id.split(path.sep).join('/');
            if (normalized.includes('/node_modules/')) {
              if (normalized.includes('/react-router-dom/') || normalized.includes('/react-router/')) {
                return 'vendor-router';
              }
              if (normalized.includes('/react-apexcharts/') || normalized.includes('/apexcharts/')) {
                return 'vendor-charts';
              }
              if (normalized.includes('/quill/')) {
                return 'vendor-editor';
              }
              if (normalized.includes('/@dnd-kit/')) {
                return 'vendor-dnd';
              }
              if (normalized.includes('/@tanstack/')) {
                return 'vendor-table';
              }
              if (normalized.includes('/node_modules/react-dom/') || normalized.includes('/node_modules/scheduler/')) {
                return 'vendor-react';
              }
              if (normalized.includes('/node_modules/react/')) {
                return 'vendor-react';
              }
              return 'vendor';
            }
            if (normalized.includes('/src/routes/PrivateAppRoutes')) {
              return 'private-app';
            }
            if (normalized.includes('/src/public')) {
              return 'public-app';
            }
            return undefined;
          },
        },
        treeshake: true,
      },
    },
    envPrefix: 'VITE_',
  };
});


