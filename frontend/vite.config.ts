import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [tailwindcss(), react(), VitePWA({
    registerType: 'autoUpdate',
    includeAssets: ['favicon.svg'],
    manifest: {
      name: 'Sports Rehab AI', short_name: 'Sports Rehab AI', start_url: '/', display: 'standalone', theme_color: '#0b1f3a', background_color: '#f6f9fc', icons: []
    }
  })],
  server: { port: 5173 },
});
