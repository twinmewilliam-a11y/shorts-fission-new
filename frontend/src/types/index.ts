// 统一类型定义

export interface Video {
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

export interface Variant {
  id: number
  video_id: number
  variant_index: number
  status: string
  title: string | null
  effects_applied: string | null
  file_path: string | null
  created_at: string
}
