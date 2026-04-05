// 统一 UI 样式常量 - RunwayML 设计系统
// 所有组件引用这些常量，确保视觉一致性

export const cn = (...classes: (string | boolean | undefined)[]) => classes.filter(Boolean).join(' ')

// 按钮样式
export const btn = {
  primary: 'bg-accent-purple hover:bg-primary-600 text-white px-4 py-2 rounded font-medium transition-all duration-200',
  secondary: 'bg-surface-raised text-text-secondary hover:text-text-primary hover:bg-white/5 border border-border-subtle px-4 py-2 rounded font-medium transition-all duration-200',
  success: 'bg-success hover:brightness-110 text-white px-4 py-2 rounded font-medium transition-all duration-200',
  danger: 'bg-error hover:brightness-110 text-white px-4 py-2 rounded font-medium transition-all duration-200',
  ghost: 'text-text-secondary hover:text-text-primary hover:bg-white/5 px-4 py-2 rounded font-medium transition-all duration-200',
  disabled: 'bg-surface-raised text-text-muted cursor-not-allowed px-4 py-2 rounded font-medium',
}

// 卡片样式
export const card = {
  base: 'bg-surface-raised rounded-lg border border-border-subtle transition-all duration-200',
  hover: 'hover:border-border-hover',
  interactive: 'bg-surface-raised rounded-lg border border-border-subtle hover:border-border-hover cursor-pointer transition-all duration-200',
}

// 弹窗样式
export const modal = {
  overlay: 'fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in',
  container: 'bg-surface-raised rounded-lg border border-border-subtle shadow-elevated max-w-lg w-full mx-4 animate-slide-up',
}

// 徽标样式
export const badge = {
  success: 'bg-success/20 text-success rounded px-2 py-0.5 text-xs font-medium',
  warning: 'bg-warning/20 text-warning rounded px-2 py-0.5 text-xs font-medium',
  error: 'bg-error/20 text-error rounded px-2 py-0.5 text-xs font-medium',
  info: 'bg-info/20 text-info rounded px-2 py-0.5 text-xs font-medium',
  neutral: 'bg-white/10 text-text-secondary rounded px-2 py-0.5 text-xs font-medium',
}

// 层级标签色
export const layerColors = {
  background: { bg: 'bg-indigo-900/50', text: 'text-indigo-300', num: 'bg-indigo-600 text-indigo-100' },
  middle: { bg: 'bg-emerald-900/50', text: 'text-emerald-300', num: 'bg-emerald-600 text-emerald-100' },
  text: { bg: 'bg-amber-900/50', text: 'text-amber-300', num: 'bg-amber-600 text-amber-100' },
}

// 输入框
export const input = {
  base: 'w-full px-4 py-2.5 bg-surface-deep border border-border-subtle rounded text-white placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-purple/50 focus:border-accent-purple transition-all',
}
