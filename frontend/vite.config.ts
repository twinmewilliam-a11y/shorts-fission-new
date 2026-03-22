import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 获取 API 基础 URL
const API_URL = process.env.VITE_API_URL || 'http://43.156.242.38:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: API_URL,
        changeOrigin: true,
      },
      '/ws': {
        target: API_URL.replace('http', 'ws'),
        ws: true,
      },
    },
  },
  define: {
    // 注入到客户端的全局变量
    __API_URL__: JSON.stringify(API_URL),
  },
})
