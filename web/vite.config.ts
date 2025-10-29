import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss({
      configPath: './tailwind.config.js',
    }),
  ],
  // Base URL for the app:
  // - Development: '/'
  // - Staging: '/' (trigpointing.me root)
  // - Production: '/app/' (trigpointing.uk/app/)
  // Set VITE_BASE_URL env var to override
  base: process.env.VITE_BASE_URL || 
        (process.env.NODE_ENV === 'production' 
          ? (process.env.VITE_ENVIRONMENT === 'production' ? '/app/' : '/')
          : '/'),
  server: {
    port: 5173,
    strictPort: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})

