
import type { Variant } from '../../types'

interface VariantListProps {
  variants: Variant[]
  selectedVariant: number | null
  onShowVariantDetail: (variant: Variant) => void
  onPreviewVariant: (variantId: number) => void
  onDownloadVariant: (variant: Variant) => void
  videoStatus?: string
  loading?: boolean
}

export function VariantList({
  variants,
  selectedVariant,
  onShowVariantDetail,
  onPreviewVariant,
  onDownloadVariant,
  videoStatus,
  loading
}: VariantListProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'downloading':
        return '⬇️'
      case 'downloaded':
        return '📥'
      case 'processing':
        return '⚙️'
      case 'completed':
        return '✅'
      case 'failed':
        return '❌'
      default:
        return '📁'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'downloading':
        return 'text-blue-400'
      case 'downloaded':
        return 'text-text-secondary'
      case 'processing':
        return 'text-yellow-400'
      case 'completed':
        return 'text-green-400'
      case 'failed':
        return 'text-red-400'
      default:
        return 'text-text-muted'
    }
  }

  return (
    <div className="space-y-4">
      <h3 className="font-bold text-text-primary">🎬 变体列表</h3>
      
      {variants.length === 0 ? (
        <div className="bg-surface-raised rounded-lg p-8 text-center text-text-secondary">
          {loading ? (
            <div className="space-y-2">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
              <p>正在加载...</p>
            </div>
          ) : videoStatus === 'processing' ? (
            <div className="space-y-2">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
              <p>正在生成变体...</p>
            </div>
          ) : videoStatus === 'completed' ? (
            <p>暂无变体数据</p>
          ) : (
            <p>等待视频下载完成后生成变体</p>
          )}
        </div>
      ) : (
        <div className="space-y-2 max-h-96 overflow-auto">
          {variants.map((variant) => (
            <div
              key={variant.id}
              className={`flex items-center gap-3 p-3 rounded-lg border ${
                selectedVariant === variant.id
                  ? 'border-blue-500 bg-blue-900/30'
                  : 'border-border-subtle hover:border-border-subtle'
              }`}
            >
              <span className="text-lg font-mono text-text-secondary">
                #{variant.variant_index}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-sm ${getStatusColor(variant.status)}`}>
                    {getStatusIcon(variant.status)}
                  </span>
                  <span className="text-sm text-text-secondary">
                    {variant.status}
                  </span>
                </div>
                {variant.effects_applied && (
                  <p className="text-xs text-text-muted truncate mt-1">
                    {variant.effects_applied}
                  </p>
                )}
              </div>
              <div className="flex gap-1">
                {variant.status === 'completed' && (
                  <>
                    <button
                      onClick={() => onShowVariantDetail(variant)}
                      className="p-2 text-text-secondary hover:text-blue-400"
                      title="查看详情"
                    >
                      📋
                    </button>
                    <button
                      onClick={() => onPreviewVariant(variant.id)}
                      className="p-2 text-text-secondary hover:text-blue-400"
                      title="预览"
                    >
                      👁️
                    </button>
                    <button
                      onClick={() => onDownloadVariant(variant)}
                      className="p-2 text-text-secondary hover:text-blue-400"
                      title="下载"
                    >
                      📥
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}