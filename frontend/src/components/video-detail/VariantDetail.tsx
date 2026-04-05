import type { Variant } from '../../types'

interface VariantDetailProps {
  variant: Variant
  onClose: () => void
  onPreviewVariant: (variantId: number) => void
  onDownloadVariant: (variant: Variant) => void
}

/**
 * 解析三层效果信息
 * 支持两种格式:
 * - 新格式: [背景层] · 效果1 · [中间层] · 效果2 · [文字层] · 效果3
 * - 旧格式: 纯文本
 */
function parseEffectLayers(effectsApplied: string | null) {
  if (!effectsApplied) {
    return {
      backgroundLayer: ['无效果信息'],
      middleLayer: ['无'],
      textLayer: ['无字幕'],
    }
  }

  if (!effectsApplied.includes('[背景层]')) {
    // 旧格式：全部当作背景层
    return {
      backgroundLayer: [effectsApplied],
      middleLayer: ['无'],
      textLayer: ['无字幕'],
    }
  }

  // 按层标记切分（保持原始逻辑）
  const bgPart = effectsApplied.split('[中间层]')[0]?.replace('[背景层]', '').trim() || ''
  const midPart = effectsApplied.split('[中间层]')[1]?.split('[文字层]')[0]?.trim() || ''
  const txtPart = effectsApplied.split('[文字层]')[1]?.trim() || ''

  return {
    backgroundLayer: bgPart.split('·').map(s => s.trim()).filter(Boolean),
    middleLayer: midPart.split('·').map(s => s.trim()).filter(Boolean).length > 0
      ? midPart.split('·').map(s => s.trim()).filter(Boolean)
      : ['无'],
    textLayer: txtPart.split('·').map(s => s.trim()).filter(Boolean).length > 0
      ? txtPart.split('·').map(s => s.trim()).filter(Boolean)
      : ['无字幕'],
  }
}

export function VariantDetail({
  variant,
  onClose,
  onPreviewVariant,
  onDownloadVariant
}: VariantDetailProps) {
  const effects = parseEffectLayers(variant.effects_applied || '')

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-[#1F2937] rounded-lg p-6 max-w-lg w-full mx-4 border border-gray-700">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-100">
            变体 #{variant.variant_index} 详情
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>
        
        {/* 三层参数显示 */}
        <div className="space-y-4">
          {/* 背景层 */}
          <div className="bg-[#374151] rounded-lg p-3">
            <h4 className="text-sm font-medium text-gray-300 mb-2 flex items-center gap-2">
              <span className="w-6 h-6 bg-indigo-600 text-indigo-100 rounded flex items-center justify-center text-xs">1</span>
              背景层（去重缓冲区）
            </h4>
            <div className="flex flex-wrap gap-2">
              {effects.backgroundLayer.map((effect, idx) => (
                <span key={idx} className="px-2 py-1 bg-indigo-900/50 text-indigo-300 rounded text-xs">
                  {effect}
                </span>
              ))}
            </div>
          </div>
          
          {/* 中间层 */}
          <div className="bg-[#374151] rounded-lg p-3">
            <h4 className="text-sm font-medium text-gray-300 mb-2 flex items-center gap-2">
              <span className="w-6 h-6 bg-green-600 text-green-100 rounded flex items-center justify-center text-xs">2</span>
              中间层（观感保护区）
            </h4>
            <div className="flex flex-wrap gap-2">
              {effects.middleLayer.map((effect, idx) => (
                <span key={idx} className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">
                  {effect}
                </span>
              ))}
            </div>
          </div>
          
          {/* 文字层 */}
          <div className="bg-[#374151] rounded-lg p-3">
            <h4 className="text-sm font-medium text-gray-300 mb-2 flex items-center gap-2">
              <span className="w-6 h-6 bg-amber-600 text-amber-100 rounded flex items-center justify-center text-xs">3</span>
              文字层（词级动画字幕）
            </h4>
            <div className="flex flex-wrap gap-2">
              {effects.textLayer.map((effect, idx) => (
                <span key={idx} className="px-2 py-1 bg-amber-900/50 text-amber-300 rounded text-xs">
                  {effect}
                </span>
              ))}
            </div>
          </div>
        </div>
        
        <div className="mt-6 flex gap-2">
          <button
            onClick={() => {
              onPreviewVariant(variant.id)
              onClose()
            }}
            className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
          >
            👁️ 预览
          </button>
          <button
            onClick={() => {
              onDownloadVariant(variant)
              onClose()
            }}
            className="flex-1 bg-gray-600 text-gray-100 py-2 rounded-lg hover:bg-gray-700"
          >
            📥 下载
          </button>
        </div>
      </div>
    </div>
  )
}
