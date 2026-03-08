import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { Videos } from './pages/Videos'
import { Downloads } from './pages/Downloads'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-100">
        {/* 导航栏 */}
        <nav className="bg-white shadow-sm sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <span className="text-2xl font-bold text-primary-600">🎬 Shorts Fission</span>
                </div>
                <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                  <NavLink
                    to="/"
                    className={({ isActive }) =>
                      `inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                        isActive
                          ? 'border-primary-500 text-gray-900'
                          : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                      }`
                    }
                  >
                    📊 仪表盘
                  </NavLink>
                  <NavLink
                    to="/videos"
                    className={({ isActive }) =>
                      `inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                        isActive
                          ? 'border-primary-500 text-gray-900'
                          : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                      }`
                    }
                  >
                    🎬 视频
                  </NavLink>
                  <NavLink
                    to="/downloads"
                    className={({ isActive }) =>
                      `inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                        isActive
                          ? 'border-primary-500 text-gray-900'
                          : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                      }`
                    }
                  >
                    📥 下载
                  </NavLink>
                </div>
              </div>
              
              {/* 移动端菜单按钮 */}
              <div className="flex items-center sm:hidden">
                <MobileMenu />
              </div>
            </div>
          </div>
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
        <footer className="mt-8 py-4 text-center text-gray-400 text-sm">
          <p>Shorts Fission · 短视频裂变系统</p>
        </footer>
      </div>
    </BrowserRouter>
  )
}

// 移动端菜单组件
function MobileMenu() {
  return (
    <div className="relative">
      <NavLink
        to="/"
        className={({ isActive }) =>
          `block px-3 py-2 text-base font-medium ${
            isActive ? 'text-primary-600' : 'text-gray-600 hover:text-gray-900'
          }`
        }
      >
        📊 仪表盘
      </NavLink>
      <NavLink
        to="/videos"
        className={({ isActive }) =>
          `block px-3 py-2 text-base font-medium ${
            isActive ? 'text-primary-600' : 'text-gray-600 hover:text-gray-900'
          }`
        }
      >
        🎬 视频
      </NavLink>
      <NavLink
        to="/downloads"
        className={({ isActive }) =>
          `block px-3 py-2 text-base font-medium ${
            isActive ? 'text-primary-600' : 'text-gray-600 hover:text-gray-900'
          }`
        }
      >
        📥 下载
      </NavLink>
    </div>
  )
}

export default App
