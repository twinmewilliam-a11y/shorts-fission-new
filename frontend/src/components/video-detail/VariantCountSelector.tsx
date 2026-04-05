
import AnimationTemplateSelector from '../AnimationTemplateSelector'

interface VariantCountSelectorProps {
  variantCount: number
  enableSubtitleLayer: boolean
  enablePlaceholderSubtitle: boolean
  targetLanguage: string
  animationTemplate: string | null
  animationPosition: string
  onVariantCountChange: (count: number) => void
  onSubtitleLayerChange: (enabled: boolean) => void
  onPlaceholderSubtitleChange: (enabled: boolean) => void
  onTargetLanguageChange: (language: string) => void
  onAnimationTemplateChange: (templateId: string | null) => void
  onAnimationPositionChange: (position: string) => void
  videoStatus?: string
  targetVariantCount?: number
  isStarting?: boolean
  onStartProcessing?: () => void
}

export function VariantCountSelector({
  variantCount,
  enableSubtitleLayer,
  enablePlaceholderSubtitle,
  targetLanguage,
  animationTemplate,
  animationPosition,
  onVariantCountChange,
  onSubtitleLayerChange,
  onPlaceholderSubtitleChange,
  onTargetLanguageChange,
  onAnimationTemplateChange,
  onAnimationPositionChange,
  videoStatus,
  targetVariantCount,
  isStarting,
  onStartProcessing
}: VariantCountSelectorProps) {
  // 仅在已下载且未设置变体数量时显示
  const shouldShowSelector = videoStatus === 'downloaded' && targetVariantCount === 0

  if (!shouldShowSelector) return null

  return (
    <div className="bg-surface-raised border border-purple-500/30 rounded-lg p-4 space-y-4">
      <div className="flex items-center gap-2 text-purple-300">
        <span className="text-xl">⚙️</span>
        <span className="font-medium">设置变体数量</span>
      </div>
      
      <div className="flex items-center gap-4">
        <label className="text-text-secondary">生成变体数量：</label>
        <input
          type="number"
          min="1"
          max="50"
          value={variantCount}
          onChange={(e) => onVariantCountChange(parseInt(e.target.value) || 1)}
          className="w-24 px-3 py-2 border border-border-subtle rounded-lg focus:ring-2 focus:ring-accent-purple/50 focus:border-accent-purple text-white bg-surface-deep"
        />
        <span className="text-text-secondary">个</span>
      </div>

      {/* Animated Caption 选项 */}
      <div className="flex items-center gap-3 pt-2">
        <input
          type="checkbox"
          id="subtitleLayer"
          checked={enableSubtitleLayer}
          onChange={(e) => onSubtitleLayerChange(e.target.checked)}
          className="w-4 h-4 text-purple-600 border-border-subtle rounded focus:ring-purple-500"
        />
        <label htmlFor="subtitleLayer" className="text-sm text-text-secondary cursor-pointer">
          📝 Animated Caption（词级动画字幕）
        </label>
      </div>

      {/* 占位字幕开关 */}
      <div className="flex items-center gap-3 pt-2">
        <input
          type="checkbox"
          id="placeholderSubtitle"
          checked={enablePlaceholderSubtitle}
          onChange={(e) => onPlaceholderSubtitleChange(e.target.checked)}
          className="w-4 h-4 text-purple-600 border-border-subtle rounded focus:ring-purple-500"
        />
        <label htmlFor="placeholderSubtitle" className="text-sm text-text-secondary cursor-pointer">
          🎬 占位字幕（无字幕视频自动添加）
        </label>
      </div>

      {/* 字幕翻译选项 */}
      <div className="flex items-center gap-3 pt-2">
        <label className="text-sm text-text-secondary">🌐 字幕翻译：</label>
        <select
          value={targetLanguage}
          onChange={(e) => onTargetLanguageChange(e.target.value)}
          className="px-3 py-1.5 border border-border-subtle rounded-lg text-text-primary bg-surface-raised text-sm"
        >
          <option value="auto">不翻译（保持原文）</option>
          <option value="en">翻译为英文</option>
          <option value="zh">翻译为中文</option>
        </select>
      </div>

      {/* 词级动画模板选择器 */}
      {enableSubtitleLayer && (
        <div className="mt-4 pt-4 border-t border-purple-500/30">
          <AnimationTemplateSelector
            templateId={animationTemplate}
            position={animationPosition}
            onTemplateChange={onAnimationTemplateChange}
            onPositionChange={onAnimationPositionChange}
          />
        </div>
      )}

      <button
        onClick={onStartProcessing}
        disabled={isStarting || variantCount <= 0}
        className="w-full bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
      >
        {isStarting ? (
          <span className="flex items-center justify-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
            启动中...
          </span>
        ) : (
          `🚀 开始生成 ${variantCount} 个变体`
        )}
      </button>
    </div>
  )
}