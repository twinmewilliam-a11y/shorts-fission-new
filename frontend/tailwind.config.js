/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ============================================
        // Design System: RunwayML-inspired cinematic dark theme
        // 适用: AI 视频处理平台
        // ============================================

        // 背景 & 表面
        surface: {
          DEFAULT: '#000000',    // 主背景 (Runway Black)
          raised: '#1a1a1a',     // 卡片/弹起表面 (Dark Surface)
          deep: '#030303',       // 层叠暗表面 (Deep Black)
          overlay: '#111111',    // 遮罩层
        },

        // 边框
        border: {
          subtle: '#27272a',     // 暗模式边框 (Border Dark)
          light: '#c9ccd1',      // 亮模式边框 (Cool Silver)
        },

        // 文字层级
        text: {
          primary: '#ffffff',    // 暗表面上的主文字
          secondary: '#767d88',  // 辅助文字 (Cool Slate)
          tertiary: '#7d848e',   // 三级文字 (Mid Slate)
          muted: '#a7a7a7',      // 弱化文字 (Muted Gray)
          heading: '#fefefe',    // 标题文字 (Near White)
        },

        // 品牌强调色（保持项目辨识度）
        accent: {
          purple: '#ec4899',     // 品牌紫（原 primary）
          blue: '#2563eb',       // 信息蓝
        },

        // 状态色
        success: '#10B981',
        warning: '#F59E0b',
        error: '#ef4444',
        info: '#3B82F6',

        // 兼容旧引用（逐步迁移后删除）
        primary: {
          50: '#fdf2f8',
          100: '#fce7f3',
          200: '#fbcfe8',
          300: '#f9a8d4',
          400: '#f472b6',
          500: '#ec4899',
          600: '#db2777',
          700: '#be185d',
          800: '#9d174d',
          900: '#831843',
        },
        dark: {
          bg: '#000000',
          card: '#1a1a1a',
          muted: '#27272a',
          border: '#27272a',
        },
      },

      fontFamily: {
        sans: ['Inter', 'Plus Jakarta Sans', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'SF Mono', 'Menlo', 'Monaco', 'monospace'],
      },

      // 圆角系统
      borderRadius: {
        'sm': '4px',
        DEFAULT: '8px',
        'lg': '12px',
        'xl': '16px',
      },

      // 间距系统（8px 基准）
      spacing: {
        '4.5': '18px',
        '13': '52px',
        '15': '60px',
        '18': '72px',
      },

      // 阴影：按 RunwayML 哲学，零阴影，只用边框
      boxShadow: {
        'none': 'none',
        'border': '0px 0px 0px 1px #27272a',
        'border-hover': '0px 0px 0px 1px #3f3f3f',
        'elevated': '0px 0px 0px 1px #27272a, 0px 2px 8px rgba(0,0,0,0.3)',
      },

      // 动画
      animation: {
        'shimmer': 'shimmer 2s infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },

      // 排版微调
      letterSpacing: {
        'tighter': '-0.9px',
        'tight': '-0.16px',
        'label': '0.35px',
      },
      lineHeight: {
        'display': '1.0',
        'tight': '1.25',
        'snug': '1.375',
      },
    },
  },
  plugins: [],
}
