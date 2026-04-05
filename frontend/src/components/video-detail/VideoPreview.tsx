import type { Video } from '../../types'

interface VideoPreviewProps {
  video: Video | null
  previewUrl: string | null
  title: string
}

export function VideoPreview({ 
  video, 
  previewUrl, 
  title
}: VideoPreviewProps) {
  return (
    <>
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
        <div className="bg-gray-800 rounded-lg overflow-hidden aspect-video relative">
          <img
            src={video.thumbnail}
            alt={title || '视频缩略图'}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30">
            <span className="text-white text-4xl">▶️</span>
          </div>
        </div>
      ) : (
        <div className="bg-gray-900 rounded-lg aspect-video flex items-center justify-center">
          <span className="text-gray-400 text-6xl">🎬</span>
        </div>
      )}
    </>
  )
}
