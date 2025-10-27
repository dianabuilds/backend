import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { find: '@ui', replacement: path.resolve(__dirname, 'src/shared/ui') },
      { find: '@icons', replacement: path.resolve(__dirname, 'src/shared/icons') },
      { find: '@shared', replacement: path.resolve(__dirname, 'src/shared') },
      { find: '@features', replacement: path.resolve(__dirname, 'src/features') },
    ],
  },
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
    setupFiles: ['./src/test/setup.ts'],
    clearMocks: true,
  },
});
