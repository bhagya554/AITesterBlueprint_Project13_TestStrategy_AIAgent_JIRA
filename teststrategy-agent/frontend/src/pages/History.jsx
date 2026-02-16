import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Trash2, Copy, FileText, Download, Calendar, Filter } from 'lucide-react'
import { historyApi, generatorApi } from '../api/client'

export default function History() {
  const [strategies, setStrategies] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('')
  const [selectedItems, setSelectedItems] = useState([])
  const navigate = useNavigate()

  useEffect(() => {
    loadStrategies()
  }, [search, filter])

  const loadStrategies = async () => {
    setLoading(true)
    try {
      const res = await historyApi.list({
        search: search || undefined,
        provider: filter || undefined,
      })
      setStrategies(res.data.items)
    } catch (e) {
      console.error('Failed to load history:', e)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this strategy?')) return
    try {
      await historyApi.delete(id)
      loadStrategies()
    } catch (e) {
      alert('Failed to delete')
    }
  }

  const handleClone = async (id) => {
    try {
      const res = await historyApi.clone(id)
      const settings = res.data.settings
      // Navigate to generator with settings
      navigate('/', { state: { cloneSettings: settings } })
    } catch (e) {
      alert('Failed to clone')
    }
  }

  const handleExportPDF = async (item) => {
    try {
      const res = await generatorApi.exportPDF({
        content: item.content,
        title: item.title,
      })
      const blob = new Blob([res.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${item.title.replace(/\s+/g, '_')}.pdf`
      a.click()
    } catch (e) {
      alert('Export failed')
    }
  }

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const formatTime = (dateStr) => {
    return new Date(dateStr).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">History</h1>
        <p className="text-gray-600">View and manage previously generated test strategies</p>
      </header>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap gap-4">
        <div className="flex-1 min-w-[300px] relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search strategies..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
        >
          <option value="">All Providers</option>
          <option value="groq">Groq</option>
          <option value="ollama">Ollama</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-500">Loading...</div>
        ) : strategies.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No strategies found</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">JIRA IDs</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Provider</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Depth</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {strategies.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="font-medium text-gray-900">{item.title}</div>
                    <div className="text-sm text-gray-500">{item.model}</div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 font-mono">
                    {item.jira_ids.length > 30 ? item.jira_ids.slice(0, 30) + '...' : item.jira_ids}
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize
                      ${item.provider === 'groq' ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800'}">
                      {item.provider}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 capitalize">{item.depth}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {formatDate(item.created_at)}
                    </div>
                    <div className="text-xs text-gray-400">{formatTime(item.created_at)}</div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleClone(item.id)}
                        className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg"
                        title="Clone & Edit"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleExportPDF(item)}
                        className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg"
                        title="Download PDF"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
