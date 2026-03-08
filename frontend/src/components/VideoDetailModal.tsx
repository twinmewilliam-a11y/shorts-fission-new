import { useState, useEffect } from 'react'
import { API_BASE_URL } from '../config'

interface Variant {
  id: number
  video_id: number
  variant_index: number
  status: string
  title: string | null
  effects_applied: string | null
  file_path: string | null
  created_at: string
}

interface Video {
  id: number
  platform: string
  video_id: string
  url: string
  title: string | null
  duration: number
  status: string
  variant_count: number
  target_variant_count: number
  download_progress: number
  variant_progress: number
  resolution?: string | null
  created_at: string
  thumbnail?: string
  source_path?: string
  error?: string
}

interface VideoDetailModalProps {
  videoId: number | null
  onClose: () => void
  onRetry?: () => void
  onStatusChange?: () => void
}

export function VideoDetailModal({ videoId, onClose, onRetry, onStatusChange }: VideoDetailModalProps) {
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

  const handleDownloadVariant = async (variantId: number) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/downloads/variant/${variantId}`)
      if (res.ok) {
        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `variant_${variantId}.mp4`
        a.click()
        window.URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('下载变体失败:', error)
    }
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
    if (!videoId || variantCount <= 0) return
    
    setIsStarting(true)
    try {
      const res = await fetch(`${API_BASE_URL}/api/videos/${videoId}/set-variant-count?count=${variantCount}`, {
        method: 'POST',
      })
      if (res.ok) {
        fetchVideoDetail()
        onStatusChange?.()
      } else {
        const error = await res.json()
        alert('启动处理失败: ' + (error.detail || '未知错误'))
      }
    } catch (error) {
      console.error('启动处理失败:', error)
      alert('启动处理失败，请检查网络')
    } finally {
      setIsStarting(false)
    }
  }

  const handleAddVariants = async (count: number) => {
    if (!videoId || count <= 0) return
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/videos/${videoId}/set-variant-count?count=${count}&append=true`, {
        method: 'POST',
      })
      if (res.ok) {
        fetchVideoDetail()
        onStatusChange?.()
        alert(`已添加 ${count} 个变体任务`)
      } else {
        const error = await res.json()
        alert('添加变体失败: ' + (error.detail || '未知错误'))
      }
    } catch (error) {
      console.error('添加变体失败:', error)
      alert('添加变体失败，请检查网络')
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
        alert('删除失败: ' + (error.detail || '未知错误'))
      }
    } catch (error) {
      console.error('删除失败:', error)
      alert('删除失败，请检查网络')
    }
  }

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
        return 'text-blue-600'
      case 'downloaded':
        return 'text-gray-600'
      case 'processing':
        return 'text-yellow-600'
      case 'completed':
        return 'text-green-600'
      case 'failed':
        return 'text-red-600'
      default:
        return 'text-gray-500'
    }
  }

  if (!videoId) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{getStatusIcon(video?.status || '')}</span>
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                {video?.title || `视频 #${videoId}`}
              </h2>
              <p className="text-sm text-gray-500">
                {video?.platform} · {video?.duration ? `${Math.floor(video.duration / 60)}:${String(video.duration % 60).padStart(2, '0')}` : '-'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-40">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* 左侧：视频信息和预览 */}
              <div className="space-y-4">
                {/* 视频预览 */}
                {previewUrl ? (
                  <div className="bg-black rounded-lg overflow-hidden aspect-video">
                    <video
                      src={previewUrl}
                      controls
                      autoPlay
                      className="w-full h-full object-contain"
                    />
                  </div>
                ) : video?.thumbnail ? (
                  <div className="bg-gray-100 rounded-lg overflow-hidden aspect-video relative">
                    <img
                      src={video.thumbnail}
                      alt={video.title || '视频缩略图'}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30">
                      <span className="text-white text-4xl">▶️</span>
                    </div>
                  </div>
                ) : (
                  <div className="bg-gray-100 rounded-lg aspect-video flex items-center justify-center">
                    <span className="text-gray-400 text-6xl">🎬</span>
                  </div>
                )}

                {/* 视频信息 */}
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-500">状态</span>
                    <span className={`font-medium ${getStatusColor(video?.status || '')}`}>
                      {getStatusIcon(video?.status || '')} {video?.status}
                    </span>
                  </div>
                  {video?.resolution && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">分辨率</span>
                      <span className="font-medium text-blue-600">{video.resolution}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-500">变体进度</span>
                    <span className="font-medium">
                      {video?.variant_count || 0} / {video?.target_variant_count || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">下载进度</span>
                    <span className="font-medium">{video?.download_progress || 0}%</span>
                  </div>
                  {video?.error && (
                    <div className="mt-2 p-2 bg-red-50 rounded text-red-600 text-sm">
                      ❌ {video.error}
                    </div>
                  )}
                </div>

                {/* 变体数量选择 - 仅在已下载且未设置变体数量时显示 */}
                {video?.status === 'downloaded' && video.target_variant_count === 0 && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 space-y-4">
                    <div className="flex items-center gap-2 text-purple-700">
                      <span className="text-xl">⚙️</span>
                      <span className="font-medium">设置变体数量</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <label className="text-gray-600">生成变体数量：</label>
                      <input
                        type="number"
                        min="1"
                        max="50"
                        value={variantCount}
                        onChange={(e) => setVariantCount(parseInt(e.target.value) || 1)}
                        className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      />
                      <span className="text-gray-500">个</span>
                    </div>
                    <button
                      onClick={handleStartProcessing}
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
                )}

                {/* 处理中状态提示 */}
                {video?.status === 'processing' && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-yellow-700">
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-yellow-600 border-t-transparent"></div>
                      <span className="font-medium">正在生成变体...</span>
                    </div>
                    <p className="text-sm text-yellow-600 mt-2">
                      已完成 {video.variant_count} / {video.target_variant_count} 个变体
                    </p>
                  </div>
                )}

                {/* 操作按钮 */}
                <div className="flex gap-2 flex-wrap">
                  {/* 继续生成变体 */}
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
                      className="flex-1 bg-yellow-500 text-white py-2 rounded-lg hover:bg-yellow-600"
                    >
                      🔄 重试
                    </button>
                  )}
                  {video?.source_path && (
                    <a
                      href={`${API_BASE_URL}/api/downloads/video/${videoId}`}
                      className="flex-1 bg-gray-100 text-gray-700 py-2 rounded-lg hover:bg-gray-200 text-center"
                    >
                      📥 下载原视频
                    </a>
                  )}
                  {/* 删除按钮 */}
                  <button
                    onClick={handleDeleteVideo}
                    className="bg-red-100 text-red-600 px-4 py-2 rounded-lg hover:bg-red-200"
                  >
                    🗑️ 删除
                  </button>
                </div>
              </div>

              {/* 右侧：变体列表 */}
              <div className="space-y-4">
                <h3 className="font-bold text-gray-900">🎬 变体列表</h3>
                
                {variants.length === 0 ? (
                  <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
                    {video?.status === 'processing' ? (
                      <div className="space-y-2">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
                        <p>正在生成变体...</p>
                      </div>
                    ) : video?.status === 'completed' ? (
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
                            ? 'border-primary-500 bg-primary-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <span className="text-lg font-mono text-gray-400">
                          #{variant.variant_index}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className={`text-sm ${getStatusColor(variant.status)}`}>
                              {getStatusIcon(variant.status)}
                            </span>
                            <span className="text-sm text-gray-500">
                              {variant.status}
                            </span>
                          </div>
                          {variant.effects_applied && (
                            <p className="text-xs text-gray-400 truncate mt-1">
                              {variant.effects_applied}
                            </p>
                          )}
                        </div>
                        <div className="flex gap-1">
                          {variant.status === 'completed' && (
                            <>
                              <button
                                onClick={() => setSelectedVariantDetail(variant)}
                                className="p-2 text-gray-400 hover:text-primary-600"
                                title="查看详情"
                              >
                                📋
                              </button>
                              <button
                                onClick={() => handlePreviewVariant(variant.id)}
                                className="p-2 text-gray-400 hover:text-primary-600"
                                title="预览"
                              >
                                👁️
                              </button>
                              <button
                                onClick={() => handleDownloadVariant(variant.id)}
                                className="p-2 text-gray-400 hover:text-primary-600"
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
            </div>
          )}
        </div>
      </div>

      {/* 新增变体弹窗 */}
      {showAddVariantsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">新增变体</h3>
              <button
                onClick={() => setShowAddVariantsModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-gray-600 text-sm">新增变体数量：</label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={additionalVariantCount}
                  onChange={(e) => setAdditionalVariantCount(parseInt(e.target.value) || 1)}
                  className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowAddVariantsModal(false)}
                  className="flex-1 bg-gray-100 text-gray-700 py-2 rounded-lg hover:bg-gray-200"
                >
                  取消
                </button>
                <button
                  onClick={() => {
                    handleAddVariants(additionalVariantCount)
                    setShowAddVariantsModal(false)
                  }}
                  className="flex-1 bg-purple-600 text-white py-2 rounded-lg hover:bg-purple-700"
                >
                  确认
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 变体详情弹窗 */}
      {selectedVariantDetail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">变体 #{selectedVariantDetail.variant_index} 详情</h3>
              <button
                onClick={() => setSelectedVariantDetail(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <span className="text-gray-500 text-sm">状态</span>
                <p className="font-medium text-green-600">✅ 已完成</p>
              </div>
              <div>
                <span className="text-gray-500 text-sm">变体组合方案</span>
                <div className="mt-1 p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-700">
                    {selectedVariantDetail.effects_applied || '无效果信息'}
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-6 flex gap-2">
              <button
                onClick={() => {
                  handlePreviewVariant(selectedVariantDetail.id)
                  setSelectedVariantDetail(null)
                }}
                className="flex-1 bg-purple-600 text-white py-2 rounded-lg hover:bg-purple-700"
              >
                👁️ 预览
              </button>
              <button
                onClick={() => {
                  handleDownloadVariant(selectedVariantDetail.id)
                  setSelectedVariantDetail(null)
                }}
                className="flex-1 bg-gray-100 text-gray-700 py-2 rounded-lg hover:bg-gray-200"
              >
                📥 下载
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
