import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Vite configuration for AniVision frontend
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy API requests to backend during development
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Rewrite not needed - backend expects /api prefix
      },
    },
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
});
