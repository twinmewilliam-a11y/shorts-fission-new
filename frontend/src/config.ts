// API 配置（从环境变量读取，构建时通过 VITE_API_URL 注入）
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
