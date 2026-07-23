import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

const djangoBaseURL = process.env.DJANGO_BASE_URL || 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      includeAssets: ['favicon-16.png', 'favicon-32.png', 'favicon-48.png', 'apple-touch-icon.png'],
      manifest: {
        name: '영업 보고 시스템 - Sales Note',
        short_name: 'Sales Note',
        description: '영업 파이프라인, 일정, 고객, 선결제를 관리하는 내부 CRM',
        lang: 'ko',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        background_color: '#f8fafc',
        theme_color: '#2563eb',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
          { src: '/icons/icon-maskable-192.png', sizes: '192x192', type: 'image/png', purpose: 'maskable' },
          { src: '/icons/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // 앱 셸(JS/CSS/HTML/아이콘)만 프리캐시한다. CRM 데이터 API는 절대 캐싱하지
        // 않는다 — 오프라인 상태에서 오래된 선결제/일정/고객 데이터를 실제 데이터처럼
        // 보여주면 위험하기 때문. 모든 /reporting/api/* 호출은 항상 네트워크로 직행.
        globPatterns: ['**/*.{js,css,html,png,svg,ico}'],
        navigateFallback: '/index.html',
        navigateFallbackDenylist: [/^\/reporting\//, /^\/todos\//, /^\/ai\//, /^\/static\//, /^\/media\//],
        cleanupOutdatedCaches: true,
        clientsClaim: true,
      },
      devOptions: {
        enabled: false,
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      '/reporting': {
        target: djangoBaseURL,
        changeOrigin: true,
      },
    },
  },
});
