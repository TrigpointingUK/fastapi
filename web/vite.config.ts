import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // Base URL for the app - set to /app/ for staging/production deployment
  // Use '/' for local development, or set APP_BASE_URL env var
  base: process.env.APP_BASE_URL || (process.env.NODE_ENV === 'production' ? '/app/' : '/'),
  server: {
    port: 5173,
    strictPort: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})

