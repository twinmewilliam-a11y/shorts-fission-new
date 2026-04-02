import { 
  Youtube, 
  Smartphone, 
  Twitter, 
  Instagram, 
  Film,
  CheckCircle, 
  XCircle,
  Clock,
  Loader2,
  Sparkles,
  Download,
  Settings,
  FileText
} from 'lucide-react'

interface VideoCardProps {
  video: {
    id: number
    platform: string
    video_id: string
    title: string | null
    duration: number
    status: string
    variant_count: number
    target_variant_count: number
    download_progress: number
    variant_progress: number
    thumbnail?: string
    resolution?: string
    has_subtitle?: boolean
    created_at: string
    stage?: string
  }
  index?: number  // 视频编号（用于显示和打包对应）
  selected?: boolean  // 是否被选中（批量操作模式）
  selectionMode?: boolean  // 是否处于选择模式
  onGenerateVariants: () => void
  onDownloadVariants?: () => void
  onSelect?: () => void
  onToggleSelect?: () => void  // 切换选中状态
}

export function VideoCard({ 
  video, 
  index,
  selected = false,
  selectionMode = false,
  onGenerateVariants, 
  onDownloadVariants,
  onSelect,
  onToggleSelect
}: VideoCardProps) {
  // 状态配置 - 深色主题
  const getStatusConfig = (status: string) => {
    const configs: Record<string, { bg: string; text: string; icon: React.ReactNode }> = {
      pending: { 
        bg: 'bg-gray-700', 
        text: 'text-gray-300',
        icon: <Clock className="w-3 h-3" />
      },
      downloading: { 
        bg: 'bg-info/20', 
        text: 'text-info',
        icon: <Loader2 className="w-3 h-3 animate-spin" />
      },
      downloaded: { 
        bg: 'bg-success/20', 
        text: 'text-success',
        icon: <CheckCircle className="w-3 h-3" />
      },
      processing: { 
        bg: 'bg-warning/20', 
        text: 'text-warning',
        icon: <Sparkles className="w-3 h-3 animate-pulse" />
      },
      completed: { 
        bg: 'bg-success', 
        text: 'text-white',
        icon: <CheckCircle className="w-3 h-3" />
      },
      failed: { 
        bg: 'bg-error/20', 
        text: 'text-error',
        icon: <XCircle className="w-3 h-3" />
      },
    }
    return configs[status] || configs.pending
  }

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      pending: '等待中',
      downloading: '下载中',
      downloaded: '已下载',
      processing: '处理中',
      completed: '已完成',
      failed: '失败',
    }
    return labels[status] || status
  }

  // 平台图标 - SVG
  const getPlatformIcon = (platform: string) => {
    const iconClass = "w-5 h-5"
    switch (platform) {
      case 'youtube':
        return <Youtube className={`${iconClass} text-red-500`} />
      case 'tiktok':
        return <Smartphone className={iconClass} />
      case 'twitter':
        return <Twitter className={`${iconClass} text-sky-400`} />
      case 'instagram':
        return <Instagram className={`${iconClass} text-pink-500`} />
      default:
        return <Film className={iconClass} />
    }
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // 分辨率显示
  const getResolutionDisplay = (resolution?: string): { text: string; className: string } | null => {
    if (!resolution) return null
    const match = resolution.match(/(\d+)/)
    if (!match) return null
    
    const height = parseInt(match[1])
    if (height >= 1080) {
      return { text: `${height}p`, className: 'bg-success/20 text-success' }
    } else if (height >= 720) {
      return { text: `${height}p`, className: 'bg-info/20 text-info' }
    } else {
      return { text: `${height}p`, className: 'bg-warning/20 text-warning' }
    }
  }

  // 获取当前处理阶段
  const getCurrentStage = () => {
    if (video.stage) return video.stage
    if (video.variant_progress < 10) return 'subtitle'
    if (video.variant_progress <= 30) return 'render'
    return 'variant'
  }

  // 预估剩余时间
  const getEstimatedTime = () => {
    const remainingVariants = video.target_variant_count - video.variant_count
    if (remainingVariants <= 0) return null
    
    const avgTimePerVariant = 45
    const remainingSeconds = remainingVariants * avgTimePerVariant
    
    if (remainingSeconds < 60) {
      return `约 ${remainingSeconds} 秒`
    } else if (remainingSeconds < 3600) {
      return `约 ${Math.ceil(remainingSeconds / 60)} 分钟`
    } else {
      const hours = Math.floor(remainingSeconds / 3600)
      const mins = Math.ceil((remainingSeconds % 3600) / 60)
      return `约 ${hours}h ${mins}m`
    }
  }

  // 获取阶段文字
  const getStageText = () => {
    const stage = getCurrentStage()
    switch (stage) {
      case 'subtitle': return '字幕提取中...'
      case 'render': return '动画渲染中...'
      default: return `变体生成 ${video.variant_count}/${video.target_variant_count}`
    }
  }

  const statusConfig = getStatusConfig(video.status)
  const canGenerate = video.status === 'downloaded'
  const canDownload = video.status === 'completed' && video.variant_count > 0
  const resolutionDisplay = getResolutionDisplay(video.resolution)
  const estimatedTime = getEstimatedTime()

  return (
    <div 
      onClick={() => {
        if (selectionMode) {
          onToggleSelect?.()
        } else {
          onSelect?.()
        }
      }}
      className={`bg-[#192134] rounded-xl border overflow-hidden cursor-pointer
        card-hover group transition-all duration-200
        ${selected ? 'ring-2 ring-primary-500 border-primary-500' : ''}
        ${video.status === 'completed' ? 'border-success/30' :
          video.status === 'processing' ? 'border-warning/30' :
          video.status === 'failed' ? 'border-error/30' :
          'border-white/10'
        }`}
    >
      {/* 缩略图区域 */}
      <div className="relative h-40 bg-[#201A32]">
        {video.thumbnail ? (
          <img
            src={video.thumbnail}
            alt={video.title || 'Video thumbnail'}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            {getPlatformIcon(video.platform)}
          </div>
        )}
        
        {/* 选择模式遮罩 */}
        {selectionMode && (
          <div className={`absolute inset-0 flex items-center justify-center transition-all duration-200
            ${selected ? 'bg-primary-500/30' : 'bg-black/30'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all
              ${selected ? 'bg-primary-500' : 'bg-gray-600/80'}`}>
              {selected ? (
                <CheckCircle className="w-5 h-5 text-white" />
              ) : (
                <div className="w-5 h-5 rounded-full border-2 border-gray-400" />
              )}
            </div>
          </div>
        )}
        
        {/* 悬停遮罩（非选择模式） */}
        {!selectionMode && (
          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 
            transition-opacity duration-200 flex items-center justify-center">
            <span className="text-white text-sm font-medium">查看详情</span>
          </div>
        )}
        
        {/* 视频编号 - 左上角 */}
        {index !== undefined && (
          <div className="absolute top-2 left-2 bg-black/70 text-white px-2.5 py-1 
            rounded-lg text-sm font-bold flex items-center gap-1.5">
            <span className="text-primary-400">#</span>
            {String(index).padStart(3, '0')}
          </div>
        )}

        {/* 状态标签 */}
        <div className="absolute top-2 right-2">
          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium
            ${statusConfig.bg} ${statusConfig.text}`}>
            {statusConfig.icon}
            <span>{getStatusLabel(video.status)}</span>
          </span>
        </div>

        {/* 平台图标（无编号时显示） */}
        {index === undefined && (
          <div className="absolute top-2 left-2 bg-black/50 rounded-full p-1.5">
            {getPlatformIcon(video.platform)}
          </div>
        )}

        {/* 时长 */}
        {video.duration > 0 && (
          <div className="absolute bottom-2 right-2 bg-black/70 text-white px-2 py-1 
            rounded text-xs font-medium">
            {formatDuration(video.duration)}
          </div>
        )}

        {/* 分辨率 + 字幕 标签组 */}
        {video.status !== 'pending' && video.status !== 'downloading' && (
          <div className="absolute bottom-2 left-2 flex gap-1.5">
            {resolutionDisplay && (
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${resolutionDisplay.className}`}>
                {resolutionDisplay.text}
              </span>
            )}
            <span className={`px-2 py-0.5 rounded text-xs font-medium flex items-center gap-1
              ${video.has_subtitle ? 'bg-success/20 text-success' : 'bg-gray-600/50 text-gray-400'}`}>
              <FileText className="w-3 h-3" />
              {video.has_subtitle ? '有字幕' : '无字幕'}
            </span>
          </div>
        )}
      </div>

      {/* 内容区域 */}
      <div className="p-4">
        <h3 className="text-sm font-medium text-white truncate mb-3 group-hover:text-primary-400 
          transition-colors" title={video.title || ''}>
          {video.title || `视频 #${video.id}`}
        </h3>

        {/* 下载进度 */}
        {video.status === 'downloading' && (
          <div className="mb-3 space-y-2">
            <div className="flex justify-between text-xs text-gray-400">
              <span className="flex items-center gap-1">
                <Loader2 className="w-3 h-3 animate-spin" />
                下载中
              </span>
              <span>{video.download_progress}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-gradient-to-r from-info to-primary-500 h-full rounded-full 
                  transition-all duration-300"
                style={{ width: `${video.download_progress}%` }}
              />
            </div>
          </div>
        )}

        {/* 处理进度 */}
        {video.status === 'processing' && (
          <div className="mb-3 space-y-3">
            <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
              <div
                className="bg-gradient-to-r from-primary-500 to-accent-500 h-full rounded-full 
                  transition-all duration-500 relative"
                style={{ width: `${video.variant_progress}%` }}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent 
                  via-white/20 to-transparent animate-shimmer" />
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary-400 animate-pulse" />
                <span className="text-xs text-gray-300 font-medium">
                  {getStageText()}
                </span>
              </div>
              <span className="text-xs text-gray-500">
                {video.variant_progress}%
              </span>
            </div>
            
            {estimatedTime && getCurrentStage() === 'variant' && (
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  预估剩余
                </span>
                <span className="text-warning font-medium">{estimatedTime}</span>
              </div>
            )}
          </div>
        )}

        {/* 完成状态 */}
        {video.status === 'completed' && (
          <div className="flex items-center gap-2 mb-3 text-sm text-success">
            <CheckCircle className="w-4 h-4" />
            <span>{video.variant_count} 个变体已生成</span>
          </div>
        )}

        {/* 待处理提示 */}
        {video.status === 'downloaded' && video.target_variant_count === 0 && (
          <div className="flex items-center gap-2 mb-3 text-sm text-primary-400">
            <Settings className="w-4 h-4" />
            <span>点击选择变体数量</span>
          </div>
        )}

        {/* 错误信息 */}
        {video.status === 'failed' && (
          <div className="flex items-center gap-2 mb-3 text-xs text-error">
            <XCircle className="w-4 h-4" />
            <span>处理失败，点击重试</span>
          </div>
        )}

        {/* 操作按钮（非选择模式） */}
        {!selectionMode && (
          <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
            {canGenerate && (
              <button
                onClick={onGenerateVariants}
                className="flex-1 bg-primary-500 hover:bg-primary-600 text-white px-3 py-2 
                  rounded-lg text-sm font-medium transition-all duration-200 
                  flex items-center justify-center gap-2 btn-hover"
              >
                <Sparkles className="w-4 h-4" />
                生成变体
              </button>
            )}
            
            {canDownload && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onDownloadVariants?.()
                }}
                className="flex-1 bg-success hover:bg-success/90 text-white px-3 py-2 
                  rounded-lg text-sm font-medium transition-all duration-200 
                  flex items-center justify-center gap-2 btn-hover"
              >
                <Download className="w-4 h-4" />
                下载全部
              </button>
            )}

            {video.status === 'processing' && (
              <button
                onClick={onSelect}
                className="flex-1 bg-warning/20 text-warning px-3 py-2 rounded-lg text-sm 
                  font-medium flex items-center justify-center gap-2"
              >
                <Loader2 className="w-4 h-4 animate-spin" />
                处理中...
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
