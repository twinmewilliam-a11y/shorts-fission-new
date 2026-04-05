import { useState, useCallback } from 'react'
import { API_BASE_URL } from '../config'
import { useToasts } from '../components/Toast'
import { Upload, CheckCircle, Loader2, FileVideo } from 'lucide-react'

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
  const { error: showError } = useToasts()
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadedVideos, setUploadedVideos] = useState<UploadedVideo[]>([])
  const [isDragOver, setIsDragOver] = useState(false)

  const uploadFiles = (files: FileList | File[]) => {
    if (!files || files.length === 0) return

    setIsUploading(true)
    setUploadProgress(0)

    const formData = new FormData()
    const fileArray = Array.from(files)
    
    fileArray.forEach(file => {
      formData.append('files', file)
    })

    const xhr = new XMLHttpRequest()

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 100)
        setUploadProgress(percent)
      }
    })

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const videos: UploadedVideo[] = JSON.parse(xhr.responseText)
          setUploadedVideos(videos)
          setUploadProgress(100)
          onUploadComplete()
        } catch {
          console.error('Failed to parse upload response')
        }
      } else {
        try {
          const error = JSON.parse(xhr.responseText)
          console.error('Upload failed:', error)
          showError('上传失败: ' + (error.detail || '未知错误'))
        } catch {
          showError('上传失败: HTTP ' + xhr.status)
        }
      }
      setIsUploading(false)
    })

    xhr.addEventListener('error', () => {
      console.error('Upload network error')
      showError('上传失败，请检查网络连接')
      setIsUploading(false)
    })

    xhr.addEventListener('abort', () => {
      console.error('Upload aborted')
      setIsUploading(false)
    })

    xhr.open('POST', `${API_BASE_URL}/api/videos/upload`)
    xhr.send(formData)
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
      {/* 上传区域 - 深色主题 */}
      <div
        className={`
          border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300
          ${isDragOver 
            ? 'border-primary-500 bg-primary-500/10 scale-[1.02]' 
            : 'border-border-subtle hover:border-border-hover hover:bg-white/5'
          }
          ${isUploading ? 'pointer-events-none opacity-60' : 'cursor-pointer'}
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
          <div className="space-y-4">
            <div className="relative w-16 h-16 mx-auto">
              <Loader2 className="w-16 h-16 text-primary-500 animate-spin" />
            </div>
            <div>
              <p className="text-white font-medium">上传中...</p>
              <p className="text-sm text-text-secondary mt-1">请稍候</p>
            </div>
            <div className="w-full max-w-xs mx-auto bg-gray-700 rounded-full h-2 overflow-hidden">
              <div 
                className="bg-gradient-to-r from-primary-500 to-primary-400 h-full rounded-full 
                  transition-all duration-300 relative"
                style={{ width: `${Math.max(uploadProgress, 2)}%` }}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent 
                  via-white/30 to-transparent animate-shimmer" />
              </div>
            </div>
            <p className="text-xs text-text-muted">{uploadProgress}%</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className={`
              w-16 h-16 mx-auto rounded-2xl flex items-center justify-center
              transition-all duration-200
              ${isDragOver ? 'bg-primary-500/20' : 'bg-white/5'}
            `}>
              <Upload className={`w-8 h-8 ${isDragOver ? 'text-primary-400' : 'text-text-secondary'}`} />
            </div>
            <div>
              <p className="text-lg text-white font-medium">
                {isDragOver ? '松开以上传' : '拖拽视频文件到这里'}
              </p>
              <p className="text-sm text-text-secondary mt-1">或点击选择文件</p>
            </div>
            <p className="text-xs text-text-muted">
              支持 MP4, MOV, AVI, MKV, WebM · 可批量上传
            </p>
          </div>
        )}
      </div>

      {/* 上传结果 - 深色主题 */}
      {uploadedVideos.length > 0 && (
        <div className="bg-success/10 border border-success/30 rounded-xl p-4">
          <div className="flex items-center gap-2 text-success font-medium mb-3">
            <CheckCircle className="w-5 h-5" />
            <span>成功上传 {uploadedVideos.length} 个视频</span>
          </div>
          <div className="space-y-2">
            {uploadedVideos.map(video => (
              <div key={video.id} className="flex items-center gap-3 text-sm">
                <FileVideo className="w-4 h-4 text-text-secondary" />
                <span className="text-text-secondary flex-1 truncate">{video.title}</span>
                {video.resolution && (
                  <span className="px-2 py-0.5 bg-info/20 text-info rounded text-xs font-medium">
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
