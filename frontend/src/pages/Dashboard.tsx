import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { API_BASE_URL } from '../config'

interface Stats {
  totalVideos: number
  completedVideos: number
  processingVideos: number
  failedVideos: number
  totalVariants: number
  pendingDownloads: number
}

interface RecentActivity {
  id: number
  type: 'download' | 'variant' | 'error'
  message: string
  time: string
  status: string
}

export function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<Stats>({
    totalVideos: 0,
    completedVideos: 0,
    processingVideos: 0,
    failedVideos: 0,
    totalVariants: 0,
    pendingDownloads: 0,
  })
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([])
  const [loading, setLoading] = useState(true)
  const [systemStatus, setSystemStatus] = useState<'healthy' | 'warning' | 'error'>('healthy')

  useEffect(() => {
    fetchStats()
    // 每30秒刷新
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/videos`)
      const data = await res.json()
      const videos = data.videos || []
      
      const newStats = {
        totalVideos: videos.length,
        completedVideos: videos.filter((v: any) => v.status === 'completed').length,
        processingVideos: videos.filter((v: any) => v.status === 'processing' || v.status === 'downloading').length,
        failedVideos: videos.filter((v: any) => v.status === 'failed').length,
        totalVariants: videos.reduce((sum: number, v: any) => sum + (v.variant_count || 0), 0),
        pendingDownloads: videos.filter((v: any) => v.status === 'pending' || v.status === 'downloading').length,
      }
      
      setStats(newStats)

      // 生成最近活动（按时间排序）
      const activities: RecentActivity[] = videos
        .sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, 10)
        .map((v: any) => ({
          id: v.id,
          type: v.status === 'failed' ? 'error' : v.status === 'completed' ? 'variant' : 'download',
          message: v.title || `视频 #${v.id}`,
          time: formatTimeAgo(new Date(v.created_at)),
          status: v.status,
        }))
      setRecentActivity(activities)

      // 系统状态
      if (videos.some((v: any) => v.status === 'failed')) {
        setSystemStatus('warning')
      } else if (videos.length === 0) {
        setSystemStatus('healthy')
      } else {
        setSystemStatus('healthy')
      }
      
      setLoading(false)
    } catch (error) {
      console.error('获取统计数据失败:', error)
      setSystemStatus('error')
      setLoading(false)
    }
  }

  const formatTimeAgo = (date: Date) => {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return '刚刚'
    if (diffMins < 60) return `${diffMins} 分钟前`
    if (diffHours < 24) return `${diffHours} 小时前`
    return `${diffDays} 天前`
  }

  const getStatusColor = () => {
    switch (systemStatus) {
      case 'healthy':
        return 'bg-green-100 text-green-800'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800'
      case 'error':
        return 'bg-red-100 text-red-800'
    }
  }

  const getStatusText = () => {
    switch (systemStatus) {
      case 'healthy':
        return '🟢 系统正常'
      case 'warning':
        return '🟡 有任务失败'
      case 'error':
        return '🔴 连接错误'
    }
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
      {/* 标题和状态 */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">📊 仪表盘</h1>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor()}`}>
          {getStatusText()}
        </span>
      </div>
      
      {/* 统计卡片 */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6 mb-8">
        <StatCard 
          title="总视频数" 
          value={stats.totalVideos} 
          icon="📹" 
          color="gray"
        />
        <StatCard 
          title="已完成" 
          value={stats.completedVideos} 
          icon="✅" 
          color="green"
        />
        <StatCard 
          title="处理中" 
          value={stats.processingVideos} 
          icon="⚙️" 
          color="blue"
        />
        <StatCard 
          title="下载中" 
          value={stats.pendingDownloads} 
          icon="⬇️" 
          color="yellow"
        />
        <StatCard 
          title="失败" 
          value={stats.failedVideos} 
          icon="❌" 
          color="red"
          highlight={stats.failedVideos > 0}
        />
        <StatCard 
          title="总变体" 
          value={stats.totalVariants} 
          icon="🎬" 
          color="purple"
        />
      </div>

      {/* 快速操作 */}
      <div className="mb-8">
        <h2 className="text-lg font-medium text-gray-900 mb-4">⚡ 快速操作</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <QuickActionCard
            title="添加视频"
            description="粘贴 YouTube 或 TikTok 链接下载视频"
            icon="📥"
            buttonText="添加单个视频"
            onClick={() => navigate('/videos')}
            color="primary"
          />
          <QuickActionCard
            title="批量下载"
            description="按账号和时间范围批量下载视频"
            icon="🔄"
            buttonText="批量下载"
            onClick={() => navigate('/downloads')}
            color="gray"
          />
          <QuickActionCard
            title="查看变体"
            description="管理已生成的视频变体"
            icon="🎞️"
            buttonText="查看视频"
            onClick={() => navigate('/videos')}
            color="purple"
          />
        </div>
      </div>

      {/* 最近活动 */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-medium text-gray-900">📋 最近活动</h2>
          <button 
            onClick={fetchStats}
            className="text-sm text-primary-600 hover:text-primary-700"
          >
            🔄 刷新
          </button>
        </div>
        
        <div className="bg-white shadow rounded-lg overflow-hidden">
          {recentActivity.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <div className="text-4xl mb-2">📭</div>
              <p>暂无活动记录</p>
              <p className="text-sm text-gray-400 mt-1">添加视频后将显示在这里</p>
            </div>
          ) : (
            <ul className="divide-y divide-gray-200">
              {recentActivity.map((activity) => (
                <li 
                  key={activity.id} 
                  className="px-6 py-4 flex items-center hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate('/videos')}
                >
                  <span className="text-2xl mr-4">
                    {activity.type === 'error' ? '❌' : activity.type === 'variant' ? '✅' : '⬇️'}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{activity.message}</p>
                    <p className="text-xs text-gray-500">{activity.time}</p>
                  </div>
                  <StatusBadge status={activity.status} />
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}

// 状态徽章组件
function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { bg: string; text: string; label: string }> = {
    pending: { bg: 'bg-gray-100', text: 'text-gray-600', label: '等待中' },
    downloading: { bg: 'bg-blue-100', text: 'text-blue-600', label: '下载中' },
    downloaded: { bg: 'bg-gray-100', text: 'text-gray-600', label: '已下载' },
    processing: { bg: 'bg-yellow-100', text: 'text-yellow-600', label: '处理中' },
    completed: { bg: 'bg-green-100', text: 'text-green-600', label: '已完成' },
    failed: { bg: 'bg-red-100', text: 'text-red-600', label: '失败' },
  }
  
  const { bg, text, label } = config[status] || config.pending
  
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${bg} ${text}`}>
      {label}
    </span>
  )
}

// 统计卡片组件
interface StatCardProps {
  title: string
  value: number
  icon: string
  color: 'gray' | 'green' | 'blue' | 'yellow' | 'red' | 'purple'
  highlight?: boolean
}

function StatCard({ title, value, icon, color, highlight }: StatCardProps) {
  const colorClasses = {
    gray: 'bg-gray-50 border-gray-200',
    green: 'bg-green-50 border-green-200',
    blue: 'bg-blue-50 border-blue-200',
    yellow: 'bg-yellow-50 border-yellow-200',
    red: 'bg-red-50 border-red-200',
    purple: 'bg-purple-50 border-purple-200',
  }

  return (
    <div className={`overflow-hidden shadow rounded-lg border ${colorClasses[color]} ${highlight ? 'ring-2 ring-red-400' : ''}`}>
      <div className="px-4 py-4 sm:px-6">
        <div className="flex items-center justify-between">
          <div>
            <dt className="text-xs font-medium text-gray-500 uppercase">{title}</dt>
            <dd className="mt-1 text-2xl font-bold text-gray-900">{value}</dd>
          </div>
          <span className="text-2xl">{icon}</span>
        </div>
      </div>
    </div>
  )
}

// 快速操作卡片组件
interface QuickActionCardProps {
  title: string
  description: string
  icon: string
  buttonText: string
  onClick: () => void
  color: 'primary' | 'gray' | 'purple'
}

function QuickActionCard({ title, description, icon, buttonText, onClick, color }: QuickActionCardProps) {
  const buttonClasses = {
    primary: 'bg-primary-600 hover:bg-primary-700 text-white',
    gray: 'bg-gray-600 hover:bg-gray-700 text-white',
    purple: 'bg-purple-600 hover:bg-purple-700 text-white',
  }

  return (
    <div className="bg-white shadow rounded-lg p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center mb-4">
        <span className="text-3xl mr-3">{icon}</span>
        <h3 className="text-lg font-medium text-gray-900">{title}</h3>
      </div>
      <p className="text-gray-500 text-sm mb-4">{description}</p>
      <button 
        onClick={onClick}
        className={`w-full px-4 py-2 rounded-md transition-colors font-medium ${buttonClasses[color]}`}
      >
        {buttonText}
      </button>
    </div>
  )
}
