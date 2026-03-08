import { useState, useCallback } from 'react'
import { API_BASE_URL } from '../config'

interface VideoUploaderProps {
  onUploadComplete: () => void
}

interface UploadedVideo {
  id: number
  title: string
  resolution: string | null
  status: string
}

export function VideoUploader({ onUploadComplete }: VideoUploaderProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadedVideos, setUploadedVideos] = useState<UploadedVideo[]>([])
  const [isDragOver, setIsDragOver] = useState(false)

  const uploadFiles = async (files: FileList | File[]) => {
    if (!files || files.length === 0) return

    setIsUploading(true)
    setUploadProgress(0)

    const formData = new FormData()
    const fileArray = Array.from(files)
    
    fileArray.forEach(file => {
      formData.append('files', file)
    })

    try {
      const response = await fetch(`${API_BASE_URL}/api/videos/upload`, {
        method: 'POST',
        body: formData,
      })

      if (response.ok) {
        const videos: UploadedVideo[] = await response.json()
        setUploadedVideos(videos)
        setUploadProgress(100)
        onUploadComplete()
      } else {
        const error = await response.json()
        console.error('Upload failed:', error)
        alert('上传失败: ' + (error.detail || '未知错误'))
      }
    } catch (err) {
      console.error('Upload error:', err)
      alert('上传失败，请检查网络连接')
    } finally {
      setIsUploading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      uploadFiles(e.target.files)
    }
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    if (e.dataTransfer.files) {
      uploadFiles(e.dataTransfer.files)
    }
  }, [])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  return (
    <div className="space-y-4">
      {/* 上传区域 */}
      <div
        className={`
          border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200
          ${isDragOver 
            ? 'border-purple-500 bg-purple-500/10' 
            : 'border-gray-600 hover:border-gray-500'
          }
          ${isUploading ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
        `}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          multiple
          accept="video/*,.mp4,.mov,.avi,.mkv,.webm"
          className="hidden"
          onChange={handleFileSelect}
          disabled={isUploading}
        />
        
        {isUploading ? (
          <div className="space-y-3">
            <div className="animate-spin w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full mx-auto"></div>
            <p className="text-gray-300">上传中...</p>
            {uploadProgress > 0 && (
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            <div className="text-5xl">📤</div>
            <div>
              <p className="text-lg text-gray-200">拖拽视频文件到这里</p>
              <p className="text-sm text-gray-400">或点击选择文件</p>
            </div>
            <p className="text-xs text-gray-500">
              支持 MP4, MOV, AVI, MKV, WebM · 可批量上传
            </p>
          </div>
        )}
      </div>

      {/* 上传结果 */}
      {uploadedVideos.length > 0 && (
        <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
          <p className="text-green-400 font-medium mb-2">
            ✅ 成功上传 {uploadedVideos.length} 个视频
          </p>
          <div className="space-y-1">
            {uploadedVideos.map(video => (
              <div key={video.id} className="text-sm text-gray-300 flex items-center gap-2">
                <span>📹 {video.title}</span>
                {video.resolution && (
                  <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs">
                    {video.resolution}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
