import { useState, useEffect } from 'react'
import { API_BASE_URL } from '../config'
import { 
  Download, 
  Calendar, 
  CalendarDays,
  Link, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  Clock,
  RefreshCw,
  Film
} from 'lucide-react'

interface DownloadItem {
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
  const [downloads, setDownloads] = useState<DownloadItem[]>([])
  const [loading, setLoading] = useState(true)
  const [batchUrl, setBatchUrl] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  useEffect(() => {
    fetchDownloads()
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
      } else {
        const error = await res.json()
        alert('批量下载失败: ' + (error.detail || '未知错误'))
      }
    } catch (error) {
      console.error('批量下载失败:', error)
      alert('批量下载失败，请检查网络连接')
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
        <Loader2 className="w-12 h-12 animate-spin text-primary-500" />
      </div>
    )
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      {/* 标题和统计 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Download className="w-7 h-7 text-primary-500" />
          批量下载
        </h1>
        <div className="flex gap-2 flex-wrap">
          {stats.downloading > 0 && (
            <span className="bg-info/20 text-info px-3 py-1 rounded-full text-sm flex items-center gap-1.5">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              {stats.downloading} 下载中
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

      {/* 批量下载表单 */}
      <div className="bg-[#192134] rounded-xl border border-white/10 p-6 mb-6">
        <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
          <CalendarDays className="w-5 h-5 text-primary-500" />
          按时间范围批量下载
        </h2>
        <p className="text-gray-400 text-sm mb-4">
          输入 YouTube/TikTok 账号链接，选择日期范围，系统将自动下载该时间段内的所有视频
        </p>
        
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-gray-300 mb-1.5">账号链接</label>
            <div className="relative">
              <Link className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="text"
                value={batchUrl}
                onChange={(e) => setBatchUrl(e.target.value)}
                placeholder="https://www.youtube.com/@username"
                className="w-full pl-10 pr-4 py-2.5 bg-[#201A32] border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">开始日期</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-[#201A32] border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">结束日期</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-[#201A32] border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
              />
            </div>
          </div>
        </div>
        
        <div className="mt-6 flex justify-end">
          <button
            onClick={handleBatchDownload}
            disabled={!batchUrl.trim()}
            className="bg-primary-500 hover:bg-primary-600 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-6 py-2.5 rounded-lg font-medium transition-all duration-200 flex items-center gap-2 btn-hover"
          >
            <Download className="w-4 h-4" />
            开始批量下载
          </button>
        </div>
      </div>

      {/* 下载列表 */}
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-medium text-white flex items-center gap-2">
          <Film className="w-5 h-5 text-gray-400" />
          下载任务
        </h2>
        <button onClick={fetchDownloads} className="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1.5 transition-colors">
          <RefreshCw className="w-4 h-4" />
          刷新
        </button>
      </div>

      {downloads.length === 0 ? (
        <div className="bg-[#192134] rounded-xl border border-white/10 p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-white/5 flex items-center justify-center">
            <Download className="w-8 h-8 text-gray-500" />
          </div>
          <p className="text-gray-400">暂无下载任务</p>
          <p className="text-sm text-gray-500 mt-1">添加批量下载任务后将显示在这里</p>
        </div>
      ) : (
        <div className="bg-[#192134] rounded-xl border border-white/10 overflow-hidden">
          <table className="min-w-full divide-y divide-white/5">
            <thead className="bg-[#201A32]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">状态</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">标题</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">平台</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">进度</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">时间</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {downloads.map((download) => (
                <tr key={download.id} className="hover:bg-white/5 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {download.status === 'completed' ? (
                        <CheckCircle className="w-5 h-5 text-success" />
                      ) : download.status === 'failed' ? (
                        <XCircle className="w-5 h-5 text-error" />
                      ) : download.status === 'downloading' ? (
                        <Loader2 className="w-5 h-5 text-info animate-spin" />
                      ) : (
                        <Clock className="w-5 h-5 text-gray-500" />
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-white truncate max-w-xs">
                      {download.title || download.url}
                    </div>
                    {download.error && (
                      <p className="text-xs text-error mt-1">{download.error}</p>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded-lg text-xs font-medium ${
                      download.platform === 'youtube' ? 'bg-red-500/20 text-red-400' :
                      download.platform === 'tiktok' ? 'bg-gray-700 text-white' :
                      'bg-gray-700 text-gray-300'
                    }`}>
                      {download.platform}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {download.status === 'downloading' ? (
                      <div className="w-full max-w-xs">
                        <div className="flex justify-between text-xs text-gray-400 mb-1">
                          <span>{download.progress}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                          <div 
                            className="bg-gradient-to-r from-info to-primary-400 h-full rounded-full transition-all duration-300"
                            style={{ width: `${download.progress}%` }}
                          />
                        </div>
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
