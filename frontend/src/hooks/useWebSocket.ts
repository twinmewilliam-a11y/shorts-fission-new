import { useEffect, useRef, useState } from 'react'

interface ProgressData {
  type: string
  video_id: number
  current: number
  total: number
  percent: number
  status: string
  current_variant?: {
    index: number
    effects: string[]
  }
}

export function useWebSocket(videoId: number | null) {
  const [progress, setProgress] = useState<ProgressData | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!videoId) return

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/progress/${videoId}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      console.log('WebSocket 连接成功')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setProgress(data)
      } catch (error) {
        console.error('解析 WebSocket 消息失败:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket 错误:', error)
      setConnected(false)
    }

    ws.onclose = () => {
      setConnected(false)
      console.log('WebSocket 连接关闭')
    }

    return () => {
      ws.close()
    }
  }, [videoId])

  const ping = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send('ping')
    }
  }

  return { progress, connected, ping }
}
