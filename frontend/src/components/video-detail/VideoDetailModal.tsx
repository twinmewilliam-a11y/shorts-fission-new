import { useState, useEffect } from 'react'
import { API_BASE_URL } from '../../config'
import { useToasts } from '../../components/Toast'
import { Video, Variant } from '../../types'


// 导入子组件
import { VideoPreview } from './VideoPreview'
import { VideoInfo } from './VideoInfo'
import { VariantCountSelector } from './VariantCountSelector'
import { ProcessingStatus } from './ProcessingStatus'
import { VariantList } from './VariantList'
import { VariantDetail } from './VariantDetail'
import { AddVariantsModal } from './AddVariantsModal'

interface VideoDetailModalProps {
  videoId: number | null
  onClose: () => void
  onRetry?: () => void
  onStatusChange?: () => void
}

export function VideoDetailModal({ videoId, onClose, onRetry, onStatusChange }: VideoDetailModalProps) {
  const { error: showError, success: showSuccess } = useToasts()
  
  // 状态管理 - 保留在父组件
  const [video, setVideo] = useState<Video | null>(null)
  const [variants, setVariants] = useState<Variant[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedVariant, setSelectedVariant] = useState<number | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [variantCount, setVariantCount] = useState(15)
  const [isStarting, setIsStarting] = useState(false)
  const [selectedVariantDetail, setSelectedVariantDetail] = useState<Variant | null>(null)
  const [showAddVariantsModal, setShowAddVariantsModal] = useState(false)
  const [additionalVariantCount, setAdditionalVariantCount] = useState(5)

  // Animated Caption 选项
  const [enableSubtitleLayer, setEnableSubtitleLayer] = useState(true)  // 默认启用
  
  // 词级动画模板
  const [animationTemplate, setAnimationTemplate] = useState<string | null>(null)  // null = 随机
  const [animationPosition, setAnimationPosition] = useState<string>('center')  // 默认屏幕中央
  
  // 占位字幕开关（无字幕视频时自动添加）
  const [enablePlaceholderSubtitle, setEnablePlaceholderSubtitle] = useState(true)  // 默认启用
  
  // 目标语言（翻译功能）
  const [targetLanguage, setTargetLanguage] = useState<string>('auto')  // 默认不翻译

  useEffect(() => {
    if (!videoId) return
    
    fetchVideoDetail()
    const interval = setInterval(fetchVideoDetail, 5000)
    return () => clearInterval(interval)
  }, [videoId])

  const fetchVideoDetail = async () => {
    if (!videoId) return
    
    try {
      // 获取视频详情
      const videoRes = await fetch(`${API_BASE_URL}/api/videos/${videoId}`)
      if (videoRes.ok) {
        const videoData = await videoRes.json()
        setVideo(videoData)
      }

      // 获取变体列表
      const variantsRes = await fetch(`${API_BASE_URL}/api/variants/${videoId}`)
      if (variantsRes.ok) {
        const variantsData = await variantsRes.json()
        setVariants(variantsData.variants || [])
      }
    } catch (error) {
      console.error('获取视频详情失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePreviewVariant = async (variantId: number) => {
    setSelectedVariant(variantId)
    // 使用下载 API 作为视频源
    setPreviewUrl(`${API_BASE_URL}/api/downloads/variant/${variantId}`)
  }

  const handleDownloadVariant = (variant: Variant) => {
    // 直接下载，避免 Fetch API 跨域问题
    // 文件名格式：{视频ID}_variant_{变体序号}.mp4
    const downloadUrl = `${API_BASE_URL}/api/downloads/variant/${variant.id}`
    const filename = `${variant.video_id}_variant_${variant.variant_index}.mp4`
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  const handleRetry = async () => {
    if (!videoId) return
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/videos/${videoId}/retry`, {
        method: 'POST',
      })
      if (res.ok) {
        fetchVideoDetail()
        onRetry?.()
      }
    } catch (error) {
      console.error('重试失败:', error)
    }
  }

  const handleStartProcessing = async () => {
    if (!videoId || variantCount <= 0 || isStarting) return

    setIsStarting(true)
    try {
      // 统一使用 Animated Caption API
      const res = await fetch(`${API_BASE_URL}/api/videos/${videoId}/set-variant-count`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          count: variantCount,
          append: false,
          enable_subtitle: enableSubtitleLayer,
          animation_template: animationTemplate,  // null = 随机
          animation_position: animationPosition,
          placeholder_subtitle_enabled: enablePlaceholderSubtitle,  // 占位字幕开关
          target_language: targetLanguage,  // 目标语言
        }),
      })
      
      if (res.ok) {
        fetchVideoDetail()
        onStatusChange?.()
      } else {
        const error = await res.json()
        showError('启动处理失败: ' + (error.detail || '未知错误'))
      }
    } catch (error) {
      console.error('启动处理失败:', error)
      showError('启动处理失败，请检查网络')
    } finally {
      setIsStarting(false)
    }
  }

  const handleAddVariants = async (count: number) => {
    if (!videoId || count <= 0) return
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/videos/${videoId}/set-variant-count`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          count: count,
          append: true,
          enable_subtitle: enableSubtitleLayer,
          animation_template: animationTemplate,
          animation_position: animationPosition,
          placeholder_subtitle_enabled: enablePlaceholderSubtitle,  // 占位字幕开关
          target_language: targetLanguage,  // 目标语言
        }),
      })
      if (res.ok) {
        fetchVideoDetail()
        onStatusChange?.()
        showSuccess(`已添加 ${count} 个变体任务`)
      } else {
        const error = await res.json()
        showError('添加变体失败: ' + (error.detail || '未知错误'))
      }
    } catch (error) {
      console.error('添加变体失败:', error)
      showError('添加变体失败，请检查网络')
    }
  }

  const handleDeleteVideo = async () => {
    if (!videoId) return
    
    if (!confirm('确定要删除这个视频及其所有变体吗？此操作不可恢复！')) {
      return
    }
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/videos/${videoId}`, {
        method: 'DELETE',
      })
      if (res.ok) {
        onClose()
        onStatusChange?.()
      } else {
        const error = await res.json()
        showError('删除失败: ' + (error.detail || '未知错误'))
      }
    } catch (error) {
      console.error('删除失败:', error)
      showError('删除失败，请检查网络')
    }
  }

  const handleDownloadVideo = () => {
    if (!videoId) return
    const downloadUrl = `${API_BASE_URL}/api/downloads/video/${videoId}`
    const a = document.createElement('a')
    a.href = downloadUrl
    a.click()
  }

  if (!videoId) return null

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-surface-raised rounded-lg shadow-elevated max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col border border-border-subtle">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border-subtle">
          <h2 className="text-xl font-bold text-text-primary">
            {video?.title || `视频 #${videoId}`}
          </h2>
          <button
            onClick={onClose}
            className="text-text-secondary hover:text-text-muted text-2xl"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-40">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* 左侧：视频信息和预览 */}
              <div className="space-y-4">
                {/* 视频预览 */}
                <VideoPreview
                  video={video}
                  previewUrl={previewUrl}
                  title={video?.title || `视频 #${videoId}`}
                />

                {/* 视频基本信息 */}
                <VideoInfo 
                  video={video}
                />

                {/* 变体数量选择器 */}
                <VariantCountSelector
                  variantCount={variantCount}
                  enableSubtitleLayer={enableSubtitleLayer}
                  enablePlaceholderSubtitle={enablePlaceholderSubtitle}
                  targetLanguage={targetLanguage}
                  animationTemplate={animationTemplate}
                  animationPosition={animationPosition}
                  onVariantCountChange={setVariantCount}
                  onSubtitleLayerChange={setEnableSubtitleLayer}
                  onPlaceholderSubtitleChange={setEnablePlaceholderSubtitle}
                  onTargetLanguageChange={setTargetLanguage}
                  onAnimationTemplateChange={setAnimationTemplate}
                  onAnimationPositionChange={setAnimationPosition}
                  videoStatus={video?.status}
                  targetVariantCount={video?.target_variant_count}
                  isStarting={isStarting}
                  onStartProcessing={handleStartProcessing}
                />

                {/* 处理中状态提示 */}
                {video?.status === 'processing' && (
                  <ProcessingStatus
                    variantProgress={video.variant_progress}
                    variantCount={video.variant_count}
                    targetVariantCount={video.target_variant_count}
                  />
                )}

                {/* 操作按钮 */}
                <div className="flex gap-2 flex-wrap">
                  {video?.status === 'completed' && (
                    <button
                      onClick={() => setShowAddVariantsModal(true)}
                      className="flex-1 bg-purple-600 text-white py-2 rounded-lg hover:bg-purple-700"
                    >
                      ➕ 继续生成变体
                    </button>
                  )}
                  {video?.status === 'failed' && (
                    <button
                      onClick={handleRetry}
                      className="flex-1 bg-yellow-600 text-white py-2 rounded-lg hover:bg-yellow-700"
                    >
                      🔄 重试
                    </button>
                  )}
                  {video?.source_path && (
                    <button
                      onClick={handleDownloadVideo}
                      className="flex-1 bg-gray-600 text-text-primary py-2 rounded-lg hover:bg-gray-700"
                    >
                      📥 下载原视频
                    </button>
                  )}
                  {/* 删除按钮 */}
                  <button
                    onClick={handleDeleteVideo}
                    className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
                  >
                    🗑️ 删除
                  </button>
                </div>
              </div>

              {/* 右侧：变体列表 */}
              <div className="space-y-4">
                <VariantList
                  variants={variants}
                  selectedVariant={selectedVariant}
                  onShowVariantDetail={setSelectedVariantDetail}
                  onPreviewVariant={handlePreviewVariant}
                  onDownloadVariant={handleDownloadVariant}
                  videoStatus={video?.status}
                  loading={loading}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 新增变体弹窗 */}
      <AddVariantsModal
        isOpen={showAddVariantsModal}
        onClose={() => setShowAddVariantsModal(false)}
        additionalVariantCount={additionalVariantCount}
        onCountChange={setAdditionalVariantCount}
        onAddVariants={handleAddVariants}
      />

      {/* 变体详情弹窗 */}
      {selectedVariantDetail && (
        <VariantDetail
          variant={selectedVariantDetail}
          onClose={() => setSelectedVariantDetail(null)}
          onPreviewVariant={handlePreviewVariant}
          onDownloadVariant={handleDownloadVariant}
        />
      )}
    </div>
  )
}