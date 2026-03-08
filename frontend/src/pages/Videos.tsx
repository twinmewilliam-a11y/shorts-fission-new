import { useState, useEffect, useCallback } from 'react'
import { VideoCard } from '../components/VideoCard'
import { VariantProgress } from '../components/VariantProgress'
import { VideoDetailModal } from '../components/VideoDetailModal'
import { VideoUploader } from '../components/VideoUploader'
import { ToastContainer, useToasts } from '../components/Toast'
import { API_BASE_URL } from '../config'

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
  created_at: string
  thumbnail?: string
  source_path?: string
  error?: string
}

export function Videos() {
  const [videos, setVideos] = useState<Video[]>([])
  const [loading, setLoading] = useState(true)
  const [videoUrl, setVideoUrl] = useState('')
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null)
  const [filter, setFilter] = useState<'all' | 'downloading' | 'downloaded' | 'processing' | 'completed' | 'failed'>('all')
  const [submitting, setSubmitting] = useState(false)
  
  const { toasts, dismissToast, success, error, warning, info } = useToasts()

  const fetchVideos = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/videos`)
      const data = await res.json()
      setVideos(data.videos || [])
    } catch (err) {
      console.error('获取视频列表失败:', err)
      error('获取视频列表失败', '请检查网络连接')
    } finally {
      setLoading(false)
    }
  }, [error])

  useEffect(() => {
    fetchVideos()
    const interval = setInterval(fetchVideos, 10000) // 每10秒刷新
    return () => clearInterval(interval)
  }, [fetchVideos])

  const handleAddVideo = async () => {
    if (!videoUrl.trim()) {
      warning('请输入视频链接')
      return
    }
    
    setSubmitting(true)
    info('正在添加视频...', videoUrl)
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/videos/single`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          url: videoUrl,
          target_variant_count: 0  // 默认不处理，需要用户在详情页选择
        }),
      })
      
      if (res.ok) {
        const data = await res.json()
        setVideoUrl('')
        fetchVideos()
        success('视频添加成功', data.title || '正在下载...')
      } else {
        const errData = await res.json().catch(() => ({}))
        error('添加视频失败', errData.detail || '请检查链接是否正确')
      }
    } catch (err) {
      console.error('添加视频失败:', err)
      error('添加视频失败', '请检查网络连接')
    } finally {
      setSubmitting(false)
    }
  }

  const handleGenerateVariants = async (videoId: number) => {
    info('开始生成变体...', '请稍候')
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/variants/${videoId}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count: 15 }),  // 默认生成15个变体
      })
      
      if (res.ok) {
        success('变体生成任务已开始')
        fetchVideos()
      } else {
        const errData = await res.json().catch(() => ({}))
        error('生成变体失败', errData.detail || '请重试')
      }
    } catch (err) {
      console.error('生成变体失败:', err)
      error('生成变体失败', '请检查网络连接')
    }
  }

  const handleDownloadVariants = async (videoId: number) => {
    info('正在打包变体...', '请稍候')
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/variants/${videoId}/download`)
      if (res.ok) {
        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `variants_${videoId}.zip`
        a.click()
        window.URL.revokeObjectURL(url)
        success('变体下载成功')
      } else {
        error('下载失败', '请重试')
      }
    } catch (err) {
      console.error('下载变体失败:', err)
      error('下载变体失败', '请检查网络连接')
    }
  }

  const handleRetryVideo = async (videoId: number) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/videos/${videoId}/retry`, {
        method: 'POST',
      })
      
      if (res.ok) {
        success('重试任务已开始')
        fetchVideos()
      } else {
        error('重试失败', '请稍后重试')
      }
    } catch (err) {
      console.error('重试失败:', err)
      error('重试失败', '请检查网络连接')
    }
  }

  const filteredVideos = videos.filter(v => filter === 'all' || v.status === filter)

  const stats = {
    total: videos.length,
    downloading: videos.filter(v => v.status === 'downloading').length,
    processing: videos.filter(v => v.status === 'processing').length,
    completed: videos.filter(v => v.status === 'completed').length,
    failed: videos.filter(v => v.status === 'failed').length,
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      {/* Toast 容器 */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
      
      {/* 标题和统计 */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">🎬 视频管理</h1>
        <div className="flex gap-2 flex-wrap">
          {stats.downloading > 0 && (
            <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
              ⬇️ {stats.downloading} 下载中
            </span>
          )}
          {stats.processing > 0 && (
            <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm">
              ⚙️ {stats.processing} 处理中
            </span>
          )}
          {stats.completed > 0 && (
            <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
              ✅ {stats.completed} 已完成
            </span>
          )}
          {stats.failed > 0 && (
            <span className="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm">
              ❌ {stats.failed} 失败
            </span>
          )}
        </div>
      </div>

      {/* 添加视频表单 */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">📥 添加视频</h2>
        
        {/* 上传区域 */}
        <VideoUploader onUploadComplete={fetchVideos} />
        
        {/* 分隔线 */}
        <div className="flex items-center gap-4 my-6">
          <div className="flex-1 border-t border-gray-200"></div>
          <span className="text-gray-400 text-sm">或者</span>
          <div className="flex-1 border-t border-gray-200"></div>
        </div>
        
        {/* URL 输入 */}
        <div className="flex flex-col gap-4 sm:flex-row">
          <input
            type="text"
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddVideo()}
            placeholder="粘贴 YouTube 或 TikTok 链接"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            disabled={submitting}
          />
          <button
            onClick={handleAddVideo}
            disabled={!videoUrl.trim() || submitting}
            className="bg-primary-600 text-white px-6 py-2 rounded-md hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {submitting ? '添加中...' : '添加视频'}
          </button>
        </div>
      </div>

      {/* 筛选器 */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {[
          { key: 'all', label: '全部', icon: '📹' },
          { key: 'downloading', label: '下载中', icon: '⬇️' },
          { key: 'downloaded', label: '已下载', icon: '📥' },
          { key: 'processing', label: '处理中', icon: '⚙️' },
          { key: 'completed', label: '已完成', icon: '✅' },
          { key: 'failed', label: '失败', icon: '❌' },
        ].map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key as typeof filter)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              filter === f.key
                ? 'bg-primary-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
            }`}
          >
            {f.icon} {f.label}
            {f.key !== 'all' && stats[f.key as keyof typeof stats] > 0 && (
              <span className="ml-1 opacity-70">
                ({stats[f.key as keyof typeof stats]})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* 视频列表 */}
      {filteredVideos.length === 0 ? (
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <div className="text-gray-400 text-6xl mb-4">📹</div>
          <p className="text-gray-500 mb-2">暂无视频</p>
          <p className="text-gray-400 text-sm">请添加视频链接开始使用</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredVideos.map((video) => (
            <VideoCard
              key={video.id}
              video={video}
              onGenerateVariants={() => handleGenerateVariants(video.id)}
              onDownloadVariants={() => handleDownloadVariants(video.id)}
              onSelect={() => setSelectedVideo(video)}
            />
          ))}
        </div>
      )}

      {/* 视频详情弹窗 */}
      {selectedVideo && (
        <VideoDetailModal
          videoId={selectedVideo.id}
          onClose={() => setSelectedVideo(null)}
          onRetry={() => {
            handleRetryVideo(selectedVideo.id)
            setSelectedVideo(null)
          }}
          onStatusChange={fetchVideos}
        />
      )}

      {/* 变体进度弹窗（旧版，保留兼容） */}
      {selectedVideo && selectedVideo.status === 'processing' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">生成变体进度</h3>
            <VariantProgress
              current={selectedVideo.variant_count}
              total={selectedVideo.target_variant_count}
              percent={selectedVideo.variant_progress}
            />
            <button
              onClick={() => setSelectedVideo(null)}
              className="mt-4 w-full bg-gray-100 text-gray-700 py-2 rounded-md hover:bg-gray-200"
            >
              关闭
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
