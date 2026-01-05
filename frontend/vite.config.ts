import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Use 'dist' for demo/production builds (Netlify), otherwise use static folder for backend
    outDir: mode === 'production' ? 'dist' : '../src/truthound_dashboard/static',
    emptyOutDir: true,
    sourcemap: false,
  },
}))
