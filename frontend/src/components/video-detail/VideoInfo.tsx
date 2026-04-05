import type { Video } from '../../types'

interface VideoInfoProps {
  video: Video | null
}

export function VideoInfo({ video }: VideoInfoProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'downloaded': return 'text-green-400'
      case 'processing': return 'text-yellow-400'
      case 'completed': return 'text-green-400'
      case 'failed': return 'text-red-400'
      default: return 'text-text-secondary'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return '⏳'
      case 'downloading': return '📥'
      case 'downloaded': return '✅'
      case 'processing': return '⚙️'
      case 'completed': return '🎉'
      case 'failed': return '❌'
      default: return '❓'
    }
  }

  return (
    <div className="bg-surface-raised rounded-lg p-4 space-y-3">
      <div className="flex justify-between">
        <span className="text-text-secondary">状态</span>
        <span className={`font-medium ${getStatusColor(video?.status || '')}`}>
          {getStatusIcon(video?.status || '')} {video?.status}
        </span>
      </div>
      {video?.resolution && (
        <div className="flex justify-between">
          <span className="text-text-secondary">分辨率</span>
          <span className="font-medium text-blue-400">{video.resolution}</span>
        </div>
      )}
      <div className="flex justify-between">
        <span className="text-text-secondary">变体进度</span>
        <span className="font-medium text-text-primary">
          {video?.variant_count || 0} / {video?.target_variant_count || 0}
        </span>
      </div>
      <div className="flex justify-between">
        <span className="text-text-secondary">下载进度</span>
        <span className="font-medium text-text-primary">{video?.download_progress || 0}%</span>
      </div>
      {video?.error && (
        <div className="mt-2 p-2 bg-red-900/30 rounded text-red-400 text-sm">
          ❌ {video.error}
        </div>
      )}
    </div>
  )
}
