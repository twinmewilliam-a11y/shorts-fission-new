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
    resolution?: string  // e.g., "720p", "1080p", "360p"
    created_at: string
  }
  onGenerateVariants: () => void
  onDownloadVariants?: () => void
  onSelect?: () => void
}

export function VideoCard({ 
  video, 
  onGenerateVariants, 
  onDownloadVariants,
  onSelect 
}: VideoCardProps) {
  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-800',
      downloading: 'bg-blue-100 text-blue-800',
      downloaded: 'bg-green-100 text-green-800',
      processing: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-500 text-white',
      failed: 'bg-red-100 text-red-800',
    }
    return colors[status] || colors.pending
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

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case 'youtube':
        return '🔴'
      case 'tiktok':
        return '📱'
      case 'twitter':
        return '🐦'
      case 'instagram':
        return '📷'
      default:
        return '🎬'
    }
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // 获取分辨率显示
  const getResolutionDisplay = (resolution?: string): { text: string; color: string; bg: string } | null => {
    if (!resolution) return null
    // 提取数字部分
    const match = resolution.match(/(\d+)/)
    if (!match) return null
    
    const height = parseInt(match[1])
    if (height >= 720) {
      return { text: `${height}p`, color: 'text-green-600', bg: 'bg-green-100' }
    } else if (height >= 480) {
      return { text: `${height}p`, color: 'text-yellow-600', bg: 'bg-yellow-100' }
    } else {
      return { text: `${height}p`, color: 'text-orange-600', bg: 'bg-orange-100' }
    }
  }

  const canGenerate = video.status === 'downloaded'
  const canDownload = video.status === 'completed' && video.variant_count > 0
  const resolutionDisplay = getResolutionDisplay(video.resolution)

  return (
    <div 
      onClick={onSelect}
      className={`bg-white rounded-lg shadow overflow-hidden border-l-4 cursor-pointer hover:shadow-lg transition-shadow ${
        video.status === 'completed' ? 'border-green-500' :
        video.status === 'processing' ? 'border-yellow-500' :
        video.status === 'failed' ? 'border-red-500' :
        'border-gray-300'
      }`}
    >
      {/* 缩略图 */}
      <div className="relative h-40 bg-gray-200">
        {video.thumbnail ? (
          <img
            src={video.thumbnail}
            alt={video.title || 'Video thumbnail'}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400 text-4xl">
            {getPlatformIcon(video.platform)}
          </div>
        )}
        
        {/* 状态标签 */}
        <div className="absolute top-2 right-2">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(video.status)}`}>
            {getStatusLabel(video.status)}
          </span>
        </div>

        {/* 平台图标 */}
        <div className="absolute top-2 left-2">
          <span className="text-lg">{getPlatformIcon(video.platform)}</span>
        </div>

        {/* 时长 */}
        {video.duration > 0 && (
          <div className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-xs">
            {formatDuration(video.duration)}
          </div>
        )}

        {/* 分辨率标签 */}
        {resolutionDisplay && video.status !== 'pending' && video.status !== 'downloading' && (
          <div className={`absolute bottom-2 left-2 ${resolutionDisplay.bg} ${resolutionDisplay.color} px-2 py-1 rounded text-xs font-medium`}>
            {resolutionDisplay.text}
          </div>
        )}
      </div>

      {/* 内容 */}
      <div className="p-4">
        <h3 className="text-sm font-medium text-gray-900 truncate mb-2" title={video.title || ''}>
          {video.title || `视频 #${video.id}`}
        </h3>

        {/* 下载进度 */}
        {video.status === 'downloading' && (
          <div className="mb-3">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>下载中</span>
              <span>{video.download_progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div
                className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                style={{ width: `${video.download_progress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* 变体进度 */}
        {video.status === 'processing' && (
          <div className="mb-3">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>生成变体</span>
              <span>{video.variant_count}/{video.target_variant_count}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div
                className="bg-yellow-500 h-1.5 rounded-full transition-all duration-300"
                style={{ width: `${video.variant_progress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* 变体数量 */}
        {video.status === 'completed' && (
          <div className="flex items-center gap-2 mb-3 text-sm text-green-600">
            <span>✅</span>
            <span>{video.variant_count} 个变体已生成</span>
          </div>
        )}

        {/* 待处理提示 */}
        {video.status === 'downloaded' && video.target_variant_count === 0 && (
          <div className="flex items-center gap-2 mb-3 text-sm text-purple-600">
            <span>⚙️</span>
            <span>点击选择变体数量</span>
          </div>
        )}

        {/* 错误信息 */}
        {video.status === 'failed' && (
          <div className="text-xs text-red-500 mb-3">
            处理失败，请重试
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
          {canGenerate && (
            <button
              onClick={onGenerateVariants}
              className="flex-1 bg-primary-600 text-white px-3 py-2 rounded-md text-sm hover:bg-primary-700 transition-colors"
            >
              🎬 生成变体
            </button>
          )}
          
          {canDownload && (
            <button
              onClick={onDownloadVariants}
              className="flex-1 bg-green-600 text-white px-3 py-2 rounded-md text-sm hover:bg-green-700 transition-colors"
            >
              📥 下载全部
            </button>
          )}

          {video.status === 'processing' && (
            <button
              onClick={onSelect}
              className="flex-1 bg-yellow-500 text-white px-3 py-2 rounded-md text-sm"
            >
              ⏳ 处理中...
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
