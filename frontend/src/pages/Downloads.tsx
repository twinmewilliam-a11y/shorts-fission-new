import { useState, useEffect } from 'react'
import { API_BASE_URL } from '../config'

interface Download {
  id: number
  url: string
  platform: string
  status: string
  progress: number
  title?: string
  error?: string
  created_at: string
  completed_at?: string
}

export function Downloads() {
  const [downloads, setDownloads] = useState<Download[]>([])
  const [loading, setLoading] = useState(true)
  const [batchUrl, setBatchUrl] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  useEffect(() => {
    fetchDownloads()
    // 每10秒刷新
    const interval = setInterval(fetchDownloads, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchDownloads = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/downloads`)
      const data = await res.json()
      setDownloads(data.downloads || [])
    } catch (error) {
      console.error('获取下载列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleBatchDownload = async () => {
    if (!batchUrl.trim()) return
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/downloads/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_url: batchUrl,
          start_date: startDate || undefined,
          end_date: endDate || undefined,
        }),
      })
      
      if (res.ok) {
        setBatchUrl('')
        setStartDate('')
        setEndDate('')
        fetchDownloads()
      }
    } catch (error) {
      console.error('批量下载失败:', error)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'downloading':
        return '⬇️'
      case 'completed':
        return '✅'
      case 'failed':
        return '❌'
      case 'pending':
        return '⏳'
      default:
        return '📁'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'downloading':
        return 'border-blue-500'
      case 'completed':
        return 'border-green-500'
      case 'failed':
        return 'border-red-500'
      default:
        return 'border-gray-300'
    }
  }

  const stats = {
    total: downloads.length,
    downloading: downloads.filter(d => d.status === 'downloading').length,
    completed: downloads.filter(d => d.status === 'completed').length,
    failed: downloads.filter(d => d.status === 'failed').length,
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
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">下载中心</h1>
        <div className="flex gap-2">
          <span className="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm">
            总计 {stats.total}
          </span>
          {stats.downloading > 0 && (
            <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
              {stats.downloading} 下载中
            </span>
          )}
        </div>
      </div>

      {/* 批量下载表单 */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">🔄 批量下载</h2>
        <p className="text-sm text-gray-500 mb-4">
          输入 YouTube/TikTok 账号链接，自动下载该账号下的所有视频
        </p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <div className="sm:col-span-2">
            <input
              type="text"
              value={batchUrl}
              onChange={(e) => setBatchUrl(e.target.value)}
              placeholder="账号链接 (如: https://www.youtube.com/@username)"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            placeholder="开始日期"
            className="px-4 py-2 border border-gray-300 rounded-md"
          />
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            placeholder="结束日期"
            className="px-4 py-2 border border-gray-300 rounded-md"
          />
        </div>
        <div className="mt-4 flex justify-end">
          <button
            onClick={handleBatchDownload}
            disabled={!batchUrl.trim()}
            className="bg-primary-600 text-white px-6 py-2 rounded-md hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            开始批量下载
          </button>
        </div>
      </div>

      {/* 下载列表 */}
      {downloads.length === 0 ? (
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <div className="text-gray-400 text-6xl mb-4">📥</div>
          <p className="text-gray-500">暂无下载任务</p>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状态
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  标题
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  平台
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  进度
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  时间
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {downloads.map((download) => (
                <tr key={download.id} className={`border-l-4 ${getStatusColor(download.status)}`}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-xl">{getStatusIcon(download.status)}</span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900 truncate max-w-xs">
                      {download.title || download.url}
                    </div>
                    {download.error && (
                      <div className="text-sm text-red-500">{download.error}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 bg-gray-100 rounded text-xs">
                      {download.platform}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {download.status === 'downloading' ? (
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${download.progress}%` }}
                        ></div>
                      </div>
                    ) : (
                      <span className="text-sm text-gray-500">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(download.created_at).toLocaleString('zh-CN')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
