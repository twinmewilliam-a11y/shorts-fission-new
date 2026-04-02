import { useState, useEffect, useCallback } from 'react'
import { VideoCard } from '../components/VideoCard'
import { VideoDetailModal } from '../components/VideoDetailModal'
import { VideoUploader } from '../components/VideoUploader'
import { ToastContainer, useToasts } from '../components/Toast'
import { API_BASE_URL } from '../config'
import { 
  Video, 
  Plus, 
  Download, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  Settings,
  Upload,
  Link,
  Trash2,
  X,
  CheckSquare,
  Square
} from 'lucide-react'

interface VideoData {
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
  stage?: string
  resolution?: string
  has_subtitle?: boolean
}

// 骨架屏组件
function VideoCardSkeleton() {
  return (
    <div className="bg-[#192134] rounded-xl border border-white/10 overflow-hidden">
      <div className="relative h-40 bg-[#201A32] skeleton" />
      <div className="p-4 space-y-3">
        <div className="h-4 bg-gray-700 rounded skeleton w-3/4" />
        <div className="h-3 bg-gray-700 rounded skeleton w-1/2" />
        <div className="h-10 bg-gray-700 rounded skeleton" />
      </div>
    </div>
  )
}

export function Videos() {
  const [videos, setVideos] = useState<VideoData[]>([])
  const [loading, setLoading] = useState(true)
  const [videoUrl, setVideoUrl] = useState('')
  const [selectedVideo, setSelectedVideo] = useState<VideoData | null>(null)
  const [filter, setFilter] = useState<'all' | 'downloading' | 'downloaded' | 'processing' | 'completed' | 'failed'>('all')
  const [submitting, setSubmitting] = useState(false)
  
  // 批量操作状态
  const [selectionMode, setSelectionMode] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [batchDeleting, setBatchDeleting] = useState(false)
  
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
    const interval = setInterval(fetchVideos, 10000)
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
          target_variant_count: 0
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
        body: JSON.stringify({ count: 15 }),
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
    // 直接下载，不打开新页面
    const downloadUrl = `${API_BASE_URL}/api/variants/${videoId}/download`
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = `#${String(videoId).padStart(3, '0')}_variants.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    success('开始下载变体', `#${videoId}`)
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

  // 批量操作：切换选择模式
  const toggleSelectionMode = () => {
    setSelectionMode(!selectionMode)
    setSelectedIds(new Set())
  }

  // 批量操作：切换单个视频选中状态
  const toggleVideoSelection = (videoId: number) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(videoId)) {
        newSet.delete(videoId)
      } else {
        newSet.add(videoId)
      }
      return newSet
    })
  }

  // 批量操作：全选/取消全选
  const toggleSelectAll = () => {
    if (selectedIds.size === filteredVideos.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(filteredVideos.map(v => v.id)))
    }
  }

  // 批量操作：批量下载（逐个触发，需要延迟等待浏览器处理）
  const handleBatchDownload = async () => {
    if (selectedIds.size === 0) {
      warning('请先选择要下载的视频')
      return
    }

    const downloadableVideos = filteredVideos
      .filter(v => selectedIds.has(v.id) && v.status === 'completed' && v.variant_count > 0)

    if (downloadableVideos.length === 0) {
      warning('所选视频中没有可下载的变体')
      return
    }

    const confirmed = confirm(
      `将下载 ${downloadableVideos.length} 个视频的变体。\n\n` +
      `注意：\n` +
      `1. 浏览器可能会询问是否允许多个下载，请点击"允许"\n` +
      `2. 下载需要间隔进行，请耐心等待\n\n` +
      `是否继续？`
    )
    
    if (!confirmed) return

    let successCount = 0

    for (let i = 0; i < downloadableVideos.length; i++) {
      const video = downloadableVideos[i]
      const downloadUrl = `${API_BASE_URL}/api/variants/${video.id}/download`
      
      try {
        // 创建临时链接并触发下载
        const a = document.createElement('a')
        a.href = downloadUrl
        a.download = `#${String(video.id).padStart(3, '0')}_variants.zip`
        a.style.display = 'none'
        document.body.appendChild(a)
        a.click()
        
        // 等待一小段时间让浏览器处理
        await new Promise(resolve => setTimeout(resolve, 100))
        
        document.body.removeChild(a)
        successCount++
        
        // 更新进度
        info(`下载进度: ${successCount}/${downloadableVideos.length}`, `#${video.id} 已触发`)
        
        // 每个下载之间等待 2 秒，让浏览器有时间处理
        if (i < downloadableVideos.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 2000))
        }
      } catch (err) {
        console.error(`下载视频 #${video.id} 失败:`, err)
      }
    }
    
    if (successCount > 0) {
      success(`已完成 ${successCount} 个下载`, '请查看浏览器下载列表')
      setSelectionMode(false)
      setSelectedIds(new Set())
    } else {
      error('批量下载失败', '请检查浏览器是否阻止了下载')
    }
  }

  // 批量操作：批量删除
  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) {
      warning('请先选择要删除的视频')
      return
    }

    if (!confirm(`确定要删除 ${selectedIds.size} 个视频吗？此操作不可恢复。`)) {
      return
    }

    setBatchDeleting(true)
    info(`正在删除 ${selectedIds.size} 个视频...`, '请稍候')

    try {
      const res = await fetch(`${API_BASE_URL}/api/videos/batch-delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_ids: Array.from(selectedIds) }),
      })

      if (res.ok) {
        const data = await res.json()
        success(`成功删除 ${data.deleted_count || selectedIds.size} 个视频`)
        setSelectionMode(false)
        setSelectedIds(new Set())
        fetchVideos()
      } else {
        const errData = await res.json().catch(() => ({}))
        error('批量删除失败', errData.detail || '请重试')
      }
    } catch (err) {
      console.error('批量删除失败:', err)
      error('批量删除失败', '请检查网络连接')
    } finally {
      setBatchDeleting(false)
    }
  }

  const filteredVideos = videos.filter(v => filter === 'all' || v.status === filter)

  const stats = {
    total: videos.length,
    downloading: videos.filter(v => v.status === 'downloading').length,
    downloaded: videos.filter(v => v.status === 'downloaded').length,
    processing: videos.filter(v => v.status === 'processing').length,
    completed: videos.filter(v => v.status === 'completed').length,
    failed: videos.filter(v => v.status === 'failed').length,
  }

  // 筛选器配置
  const filterOptions = [
    { key: 'all', label: '全部', icon: Video },
    { key: 'downloading', label: '下载中', icon: Download },
    { key: 'downloaded', label: '已下载', icon: CheckCircle },
    { key: 'processing', label: '处理中', icon: Settings },
    { key: 'completed', label: '已完成', icon: CheckCircle },
    { key: 'failed', label: '失败', icon: XCircle },
  ] as const

  if (loading) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="flex justify-between items-center mb-6">
          <div className="h-8 w-48 bg-gray-700 rounded skeleton" />
          <div className="flex gap-2">
            <div className="h-6 w-24 bg-gray-700 rounded-full skeleton" />
            <div className="h-6 w-24 bg-gray-700 rounded-full skeleton" />
          </div>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <VideoCardSkeleton key={i} />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
      
      {/* 标题和统计 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Video className="w-7 h-7 text-primary-500" />
          视频管理
        </h1>
        <div className="flex gap-2 flex-wrap items-center">
          {/* 统计标签 */}
          {stats.downloading > 0 && (
            <span className="bg-info/20 text-info px-3 py-1 rounded-full text-sm flex items-center gap-1.5">
              <Download className="w-3.5 h-3.5" />
              {stats.downloading} 下载中
            </span>
          )}
          {stats.processing > 0 && (
            <span className="bg-warning/20 text-warning px-3 py-1 rounded-full text-sm flex items-center gap-1.5">
              <Settings className="w-3.5 h-3.5 animate-spin" />
              {stats.processing} 处理中
            </span>
          )}
          {stats.completed > 0 && (
            <span className="bg-success/20 text-success px-3 py-1 rounded-full text-sm flex items-center gap-1.5">
              <CheckCircle className="w-3.5 h-3.5" />
              {stats.completed} 已完成
            </span>
          )}
          {stats.failed > 0 && (
            <span className="bg-error/20 text-error px-3 py-1 rounded-full text-sm flex items-center gap-1.5">
              <XCircle className="w-3.5 h-3.5" />
              {stats.failed} 失败
            </span>
          )}
        </div>
      </div>

      {/* 添加视频表单 */}
      <div className="bg-[#192134] rounded-xl border border-white/10 p-6 mb-6">
        <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5 text-primary-500" />
          添加视频
        </h2>
        
        <VideoUploader onUploadComplete={fetchVideos} />
        
        <div className="flex items-center gap-4 my-6">
          <div className="flex-1 border-t border-white/10"></div>
          <span className="text-gray-500 text-sm">或者</span>
          <div className="flex-1 border-t border-white/10"></div>
        </div>
        
        <div className="flex flex-col gap-4 sm:flex-row">
          <div className="flex-1 relative">
            <Link className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="text"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddVideo()}
              placeholder="粘贴 YouTube 或 TikTok 链接"
              className="w-full pl-10 pr-4 py-2.5 bg-[#201A32] border border-white/10 rounded-lg
                text-white placeholder-gray-500 focus:outline-none focus:ring-2 
                focus:ring-primary-500/50 focus:border-primary-500 transition-all"
              disabled={submitting}
            />
          </div>
          <button
            onClick={handleAddVideo}
            disabled={!videoUrl.trim() || submitting}
            className="bg-primary-500 hover:bg-primary-600 disabled:bg-gray-700 
              disabled:cursor-not-allowed text-white px-6 py-2.5 rounded-lg 
              font-medium transition-all duration-200 flex items-center justify-center gap-2
              btn-hover"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                添加中...
              </>
            ) : (
              <>
                <Plus className="w-4 h-4" />
                添加视频
              </>
            )}
          </button>
        </div>
      </div>

      {/* 筛选器和批量操作 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        {/* 筛选器 */}
        <div className="flex gap-2 flex-wrap">
          {filterOptions.map((f) => {
            const Icon = f.icon
            const count = f.key !== 'all' ? stats[f.key] : 0
            const isActive = filter === f.key
            
            return (
              <button
                key={f.key}
                onClick={() => setFilter(f.key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                  flex items-center gap-2 btn-hover
                  ${isActive
                    ? 'bg-primary-500 text-white'
                    : 'bg-[#192134] text-gray-400 hover:text-white hover:bg-white/10 border border-white/10'
                  }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? '' : 'text-gray-500'}`} />
                {f.label}
                {count > 0 && (
                  <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                    isActive ? 'bg-white/20' : 'bg-white/10'
                  }`}>
                    {count}
                  </span>
                )}
              </button>
            )
          })}
        </div>

        {/* 批量操作按钮 */}
        <div className="flex gap-2">
          {selectionMode ? (
            <>
              <button
                onClick={toggleSelectAll}
                className="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                  flex items-center gap-2 btn-hover bg-[#192134] text-gray-300 
                  hover:text-white border border-white/10"
              >
                {selectedIds.size === filteredVideos.length ? (
                  <>
                    <CheckSquare className="w-4 h-4" />
                    取消全选
                  </>
                ) : (
                  <>
                    <Square className="w-4 h-4" />
                    全选
                  </>
                )}
              </button>
              <button
                onClick={handleBatchDownload}
                disabled={selectedIds.size === 0}
                className="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                  flex items-center gap-2 btn-hover bg-success hover:bg-success/90
                  disabled:bg-gray-700 disabled:cursor-not-allowed text-white"
              >
                <Download className="w-4 h-4" />
                批量下载 ({selectedIds.size})
              </button>
              <button
                onClick={handleBatchDelete}
                disabled={selectedIds.size === 0 || batchDeleting}
                className="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                  flex items-center gap-2 btn-hover bg-error hover:bg-error/90
                  disabled:bg-gray-700 disabled:cursor-not-allowed text-white"
              >
                {batchDeleting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    删除中...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    批量删除 ({selectedIds.size})
                  </>
                )}
              </button>
              <button
                onClick={toggleSelectionMode}
                className="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                  flex items-center gap-2 btn-hover bg-gray-700 hover:bg-gray-600 text-white"
              >
                <X className="w-4 h-4" />
                取消
              </button>
            </>
          ) : (
            <button
              onClick={toggleSelectionMode}
              className="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                flex items-center gap-2 btn-hover bg-[#192134] text-gray-300 
                hover:text-white border border-white/10"
            >
              <CheckSquare className="w-4 h-4" />
              批量操作
            </button>
          )}
        </div>
      </div>

      {/* 视频列表 */}
      {filteredVideos.length === 0 ? (
        <div className="bg-[#192134] rounded-xl border border-white/10 p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-white/5 flex items-center justify-center">
            <Video className="w-8 h-8 text-gray-500" />
          </div>
          <p className="text-gray-300 mb-2 font-medium">暂无视频</p>
          <p className="text-gray-500 text-sm">请添加视频链接或上传视频文件开始使用</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredVideos.map((video) => (
            <VideoCard
              key={video.id}
              video={video}
              index={video.id}
              selected={selectedIds.has(video.id)}
              selectionMode={selectionMode}
              onGenerateVariants={() => handleGenerateVariants(video.id)}
              onDownloadVariants={() => handleDownloadVariants(video.id)}
              onSelect={() => setSelectedVideo(video)}
              onToggleSelect={() => toggleVideoSelection(video.id)}
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
    </div>
  )
}
