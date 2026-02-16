import { Routes, Route, NavLink } from 'react-router-dom'
import { Beaker, History as HistoryIcon, Settings as SettingsIcon, Menu, X } from 'lucide-react'
import { useState, useEffect } from 'react'
import Generator from './pages/Generator'
import History from './pages/History'
import Settings from './pages/Settings'
import { llmApi } from './api/client'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [llmStatus, setLlmStatus] = useState({ connected: false, loading: true })
  const [jiraUrl, setJiraUrl] = useState('')

  useEffect(() => {
    checkConnections()
  }, [])

  const checkConnections = async () => {
    try {
      const providersRes = await llmApi.getProviders()
      const providers = providersRes.data
      const anyConnected = providers.some(p => p.connected)
      setLlmStatus({ connected: anyConnected, loading: false })
    } catch (e) {
      setLlmStatus({ connected: false, loading: false })
    }
  }

  const navItems = [
    { to: '/', label: 'Generator', icon: Beaker },
    { to: '/history', label: 'History', icon: HistoryIcon },
    { to: '/settings', label: 'Settings', icon: SettingsIcon },
  ]

  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      {/* Mobile header */}
      <div className="md:hidden bg-navy-900 text-white p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Beaker className="w-6 h-6" />
          <span className="font-bold text-lg">TestStrategy Agent</span>
        </div>
        <button onClick={() => setSidebarOpen(!sidebarOpen)}>
          {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Sidebar */}
      <aside className={`
        fixed md:static inset-y-0 left-0 z-50 w-64 bg-navy-900 text-white flex flex-col
        transform transition-transform duration-200 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        <div className="p-6 border-b border-navy-800">
          <div className="flex items-center gap-3">
            <Beaker className="w-8 h-8 text-primary-400" />
            <div>
              <h1 className="font-bold text-xl">TestStrategy</h1>
              <p className="text-xs text-navy-300">AI-Powered Document Generator</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => `
                flex items-center gap-3 px-4 py-3 rounded-lg transition-colors
                ${isActive 
                  ? 'bg-primary-600 text-white' 
                  : 'text-navy-200 hover:bg-navy-800 hover:text-white'}
              `}
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-navy-800">
          <div className="flex items-center gap-2 mb-2">
            <div className={`w-2 h-2 rounded-full ${llmStatus.connected ? 'bg-green-400' : 'bg-red-400'}`} />
            <span className="text-sm text-navy-300">
              {llmStatus.loading ? 'Checking...' : llmStatus.connected ? 'LLM Connected' : 'LLM Disconnected'}
            </span>
          </div>
          {jiraUrl && (
            <div className="text-xs text-navy-400 truncate">
              {jiraUrl}
            </div>
          )}
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<Generator />} />
          <Route path="/history" element={<History />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
