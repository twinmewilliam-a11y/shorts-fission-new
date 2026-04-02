import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { Film, LayoutDashboard, Video, Download, Menu, X } from 'lucide-react'
import { useState } from 'react'
import { Dashboard } from './pages/Dashboard'
import { Videos } from './pages/Videos'
import { Downloads } from './pages/Downloads'

function App() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#0F172A]">
        {/* 导航栏 - 深色 */}
        <nav className="bg-[#192134] border-b border-white/10 sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center gap-2">
                  <Film className="w-8 h-8 text-primary-500" />
                  <span className="text-xl font-bold text-white">Shorts Fission</span>
                </div>
                <div className="hidden sm:ml-8 sm:flex sm:space-x-1">
                  <NavLink
                    to="/"
                    className={({ isActive }) =>
                      `inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                        isActive
                          ? 'bg-primary-500/20 text-primary-400'
                          : 'text-gray-400 hover:text-white hover:bg-white/5'
                      }`
                    }
                  >
                    <LayoutDashboard className="w-4 h-4" />
                    仪表盘
                  </NavLink>
                  <NavLink
                    to="/videos"
                    className={({ isActive }) =>
                      `inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                        isActive
                          ? 'bg-primary-500/20 text-primary-400'
                          : 'text-gray-400 hover:text-white hover:bg-white/5'
                      }`
                    }
                  >
                    <Video className="w-4 h-4" />
                    视频
                  </NavLink>
                  <NavLink
                    to="/downloads"
                    className={({ isActive }) =>
                      `inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                        isActive
                          ? 'bg-primary-500/20 text-primary-400'
                          : 'text-gray-400 hover:text-white hover:bg-white/5'
                      }`
                    }
                  >
                    <Download className="w-4 h-4" />
                    下载
                  </NavLink>
                </div>
              </div>
              
              {/* 移动端菜单按钮 */}
              <div className="flex items-center sm:hidden">
                <button 
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="p-2 text-gray-400 hover:text-white transition-colors"
                >
                  {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                </button>
              </div>
            </div>
          </div>
          
          {/* 移动端菜单 */}
          {mobileMenuOpen && (
            <div className="sm:hidden border-t border-white/10 bg-[#192134]">
              <NavLink
                to="/"
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 text-base font-medium transition-colors ${
                    isActive ? 'bg-primary-500/20 text-primary-400' : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`
                }
              >
                <LayoutDashboard className="w-5 h-5" />
                仪表盘
              </NavLink>
              <NavLink
                to="/videos"
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 text-base font-medium transition-colors ${
                    isActive ? 'bg-primary-500/20 text-primary-400' : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`
                }
              >
                <Video className="w-5 h-5" />
                视频
              </NavLink>
              <NavLink
                to="/downloads"
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 text-base font-medium transition-colors ${
                    isActive ? 'bg-primary-500/20 text-primary-400' : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`
                }
              >
                <Download className="w-5 h-5" />
                下载
              </NavLink>
            </div>
          )}
        </nav>

        {/* 页面内容 */}
        <main className="max-w-7xl mx-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/videos" element={<Videos />} />
            <Route path="/downloads" element={<Downloads />} />
          </Routes>
        </main>
        
        {/* 页脚 */}
        <footer className="mt-8 py-6 text-center text-gray-500 text-sm border-t border-white/5">
          <p>Shorts Fission · 短视频裂变系统</p>
        </footer>
      </div>
    </BrowserRouter>
  )
}

export default App
