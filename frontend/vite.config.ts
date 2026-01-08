import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import { intlayer } from 'vite-intlayer'
import path from 'path'

// Custom plugin to resolve .intlayer paths
const intlayerPathResolver = (): Plugin => ({
  name: 'intlayer-path-resolver',
  enforce: 'pre',
  resolveId(source, importer) {
    // Match patterns like ../../.intlayer/dictionary/xxx.json
    if (source.includes('.intlayer/dictionary/') && importer) {
      const jsonFile = source.split('.intlayer/dictionary/')[1]
      return path.resolve(__dirname, '.intlayer/dictionary', jsonFile)
    }
    return null
  },
})

export default defineConfig(({ mode }) => ({
  plugins: [intlayerPathResolver(), react(), intlayer()],
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
    // demo: Netlify (dist/), pip: backend static folder
    outDir: mode === 'demo' ? 'dist' : '../src/truthound_dashboard/static',
    emptyOutDir: true,
    sourcemap: false,
  },
  // pip: exclude mockServiceWorker.js, demo: include all
  publicDir: mode === 'pip' ? 'public-pip' : 'public',
}))
