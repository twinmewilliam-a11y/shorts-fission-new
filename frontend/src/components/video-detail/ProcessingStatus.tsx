

interface ProcessingStatusProps {
  variantProgress: number
  variantCount: number
  targetVariantCount: number
}

export function ProcessingStatus({ 
  variantProgress, 
  variantCount, 
  targetVariantCount 
}: ProcessingStatusProps) {
  const remainingVariants = targetVariantCount - variantCount
  const avgTimePerVariant = 45 // 秒/变体
  const remainingSeconds = remainingVariants * avgTimePerVariant

  const formatTime = (seconds: number) => {
    if (seconds < 60) {
      return `约 ${seconds} 秒`
    } else if (seconds < 3600) {
      return `约 ${Math.ceil(seconds / 60)} 分钟`
    } else {
      const hours = Math.floor(seconds / 3600)
      const mins = Math.ceil((seconds % 3600) / 60)
      return `约 ${hours} 小时 ${mins} 分钟`
    }
  }

  const getProgressText = (progress: number) => {
    if (progress < 30) return "📝 正在提取字幕和生成动画..."
    if (progress < 70) return "🎬 正在生成视频变体..."
    if (progress < 95) return "✨ 即将完成，请稍候..."
    return "🎉 正在最后处理..."
  }

  return (
    <div className="bg-gradient-to-r from-yellow-900/20 to-amber-900/20 border border-yellow-700/50 rounded-lg p-4 space-y-3">
      {/* 标题行 */}
      <div className="flex items-center gap-2">
        <div className="animate-spin rounded-full h-5 w-5 border-2 border-yellow-400 border-t-transparent"></div>
        <span className="font-medium text-yellow-300">正在生成变体...</span>
      </div>
      
      {/* 进度条 */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-text-secondary">
          <span>完成度</span>
          <span className="font-bold text-yellow-300">{variantProgress}%</span>
        </div>
        <div className="w-full bg-yellow-900/30 rounded-full h-3">
          <div
            className="bg-gradient-to-r from-yellow-400 to-amber-400 h-3 rounded-full transition-all duration-500 relative overflow-hidden"
            style={{ width: `${variantProgress}%` }}
          >
            {/* 动画效果 */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-pulse"></div>
          </div>
        </div>
      </div>
      
      {/* 详细信息 */}
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div className="bg-surface-raised rounded p-2">
          <div className="text-text-secondary text-xs">已完成</div>
          <div className="font-bold text-yellow-300">{variantCount} 个</div>
        </div>
        <div className="bg-surface-raised rounded p-2">
          <div className="text-text-secondary text-xs">剩余</div>
          <div className="font-bold text-amber-300">{remainingVariants} 个</div>
        </div>
      </div>
      
      {/* 预估剩余时间 */}
      <div className="bg-surface-raised/70 rounded p-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">⏱️</span>
          <span className="text-text-secondary text-sm">预估剩余时间</span>
        </div>
        <span className="font-bold text-amber-300">
          {formatTime(remainingSeconds)}
        </span>
      </div>
      
      {/* 进度阶段提示 */}
      <div className="text-xs text-text-secondary text-center">
        {getProgressText(variantProgress)}
      </div>
    </div>
  )
}