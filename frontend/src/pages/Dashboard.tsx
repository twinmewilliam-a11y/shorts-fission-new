import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { API_BASE_URL } from '../config'
import { 
  LayoutDashboard, 
  Video, 
  CheckCircle, 
  Settings, 
  Download, 
  XCircle, 
  Sparkles,
  TrendingUp,
  Activity,
  RefreshCw,
  Plus,
  ArrowRight,
  Film,
  Loader2,
  Inbox
} from 'lucide-react'

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
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/videos`)
      const data = await res.json()
      const videos = data.videos || []
      
      setStats({
        totalVideos: videos.length,
        completedVideos: videos.filter((v: any) => v.status === 'completed').length,
        processingVideos: videos.filter((v: any) => v.status === 'processing' || v.status === 'downloading').length,
        failedVideos: videos.filter((v: any) => v.status === 'failed').length,
        totalVariants: videos.reduce((sum: number, v: any) => sum + (v.variant_count || 0), 0),
        pendingDownloads: videos.filter((v: any) => v.status === 'pending' || v.status === 'downloading').length,
      })

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

      if (videos.some((v: any) => v.status === 'failed')) {
        setSystemStatus('warning')
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-12 h-12 animate-spin text-primary-500" />
      </div>
    )
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      {/* 标题和状态 */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <LayoutDashboard className="w-7 h-7 text-primary-500" />
          仪表盘
        </h1>
        <div className={`px-3 py-1.5 rounded-full text-sm font-medium flex items-center gap-1.5 ${
          systemStatus === 'healthy' ? 'bg-success/20 text-success' :
          systemStatus === 'warning' ? 'bg-warning/20 text-warning' :
          'bg-error/20 text-error'
        }`}>
          <span className={`w-2 h-2 rounded-full ${
            systemStatus === 'healthy' ? 'bg-success' :
            systemStatus === 'warning' ? 'bg-warning' : 'bg-error'
          }`} />
          {systemStatus === 'healthy' ? '系统正常' : 
           systemStatus === 'warning' ? '有任务失败' : '连接错误'}
        </div>
      </div>
      
      {/* 统计卡片 */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6 mb-8">
        <StatCard title="总视频数" value={stats.totalVideos} icon={Film} color="gray" />
        <StatCard title="已完成" value={stats.completedVideos} icon={CheckCircle} color="green" />
        <StatCard title="处理中" value={stats.processingVideos} icon={Settings} color="blue" />
        <StatCard title="下载中" value={stats.pendingDownloads} icon={Download} color="yellow" />
        <StatCard title="失败" value={stats.failedVideos} icon={XCircle} color="red" highlight={stats.failedVideos > 0} />
        <StatCard title="总变体" value={stats.totalVariants} icon={Sparkles} color="purple" />
      </div>

      {/* 快速操作 */}
      <div className="mb-8">
        <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-gray-400" />
          快速操作
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <QuickActionCard title="添加视频" description="粘贴 YouTube 或 TikTok 链接下载视频" icon={Plus} buttonText="添加单个视频" onClick={() => navigate('/videos')} color="primary" />
          <QuickActionCard title="批量下载" description="按账号和时间范围批量下载视频" icon={Download} buttonText="批量下载" onClick={() => navigate('/downloads')} color="gray" />
          <QuickActionCard title="查看变体" description="管理已生成的视频变体" icon={Video} buttonText="查看视频" onClick={() => navigate('/videos')} color="purple" />
        </div>
      </div>

      {/* 最近活动 */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-medium text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-gray-400" />
            最近活动
          </h2>
          <button onClick={fetchStats} className="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1.5 transition-colors">
            <RefreshCw className="w-4 h-4" />
            刷新
          </button>
        </div>
        
        <div className="bg-[#192134] rounded-xl border border-white/10 overflow-hidden">
          {recentActivity.length === 0 ? (
            <div className="p-8 text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-white/5 flex items-center justify-center">
                <Inbox className="w-8 h-8 text-gray-500" />
              </div>
              <p className="text-gray-400">暂无活动记录</p>
              <p className="text-sm text-gray-500 mt-1">添加视频后将显示在这里</p>
            </div>
          ) : (
            <ul className="divide-y divide-white/5">
              {recentActivity.map((activity) => (
                <li key={activity.id} className="px-6 py-4 flex items-center hover:bg-white/5 cursor-pointer transition-colors" onClick={() => navigate('/videos')}>
                  <div className="flex-shrink-0 mr-4">
                    {activity.type === 'error' ? (
                      <XCircle className="w-5 h-5 text-error" />
                    ) : activity.type === 'variant' ? (
                      <CheckCircle className="w-5 h-5 text-success" />
                    ) : (
                      <Download className="w-5 h-5 text-info" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{activity.message}</p>
                    <p className="text-xs text-gray-500 mt-1">{activity.time}</p>
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

// 状态徽章
function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { bg: string; text: string; label: string }> = {
    pending: { bg: 'bg-gray-700', text: 'text-gray-300', label: '等待中' },
    downloading: { bg: 'bg-info/20', text: 'text-info', label: '下载中' },
    downloaded: { bg: 'bg-gray-700', text: 'text-gray-300', label: '已下载' },
    processing: { bg: 'bg-warning/20', text: 'text-warning', label: '处理中' },
    completed: { bg: 'bg-success/20', text: 'text-success', label: '已完成' },
    failed: { bg: 'bg-error/20', text: 'text-error', label: '失败' },
  }
  const { bg, text, label } = config[status] || config.pending
  return <span className={`px-2 py-1 rounded-lg text-xs font-medium ${bg} ${text}`}>{label}</span>
}

// 统计卡片
interface StatCardProps {
  title: string
  value: number
  icon: React.ComponentType<{ className?: string }>
  color: 'gray' | 'green' | 'blue' | 'yellow' | 'red' | 'purple'
  highlight?: boolean
}

function StatCard({ title, value, icon: Icon, color, highlight }: StatCardProps) {
  const colorClasses = {
    gray: 'bg-[#201A32] border-gray-700',
    green: 'bg-success/10 border-success/30',
    blue: 'bg-info/10 border-info/30',
    yellow: 'bg-warning/10 border-warning/30',
    red: 'bg-error/10 border-error/30',
    purple: 'bg-purple-500/10 border-purple-500/50',
  }

  return (
    <div className={`rounded-xl border overflow-hidden ${colorClasses[color]} ${highlight ? 'ring-2 ring-error/50' : ''}`}>
      <div className="px-4 py-4 sm:px-6">
        <div className="flex items-center justify-between">
          <div>
            <dt className="text-xs font-medium text-gray-400 uppercase">{title}</dt>
            <dd className="mt-1 text-2xl font-bold text-white">{value}</dd>
          </div>
          <Icon className="w-6 h-6 text-gray-400" />
        </div>
      </div>
    </div>
  )
}

// 快速操作卡片
interface QuickActionCardProps {
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  buttonText: string
  onClick: () => void
  color: 'primary' | 'gray' | 'purple'
}

function QuickActionCard({ title, description, icon: Icon, buttonText, onClick, color }: QuickActionCardProps) {
  const buttonClasses = {
    primary: 'bg-primary-500 hover:bg-primary-600 text-white',
    gray: 'bg-gray-600 hover:bg-gray-500 text-white',
    purple: 'bg-purple-500 hover:bg-purple-600 text-white',
  }

  return (
    <div className="bg-[#192134] rounded-xl border border-white/10 p-6 hover:border-white/20 transition-all duration-200">
      <div className="flex items-center mb-4">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center mr-3 ${
          color === 'primary' ? 'bg-primary-500/20' : color === 'gray' ? 'bg-gray-700/50' : 'bg-purple-500/20'
        }`}>
          <Icon className={`w-5 h-5 ${color === 'primary' ? 'text-primary-400' : 'text-gray-400'}`} />
        </div>
        <h3 className="text-lg font-medium text-white">{title}</h3>
      </div>
      <p className="text-gray-400 text-sm mb-4">{description}</p>
      <button onClick={onClick} className={`w-full px-4 py-2.5 rounded-lg transition-all duration-200 font-medium flex items-center justify-center gap-2 btn-hover ${buttonClasses[color]}`}>
        {buttonText}
        <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  )
}
