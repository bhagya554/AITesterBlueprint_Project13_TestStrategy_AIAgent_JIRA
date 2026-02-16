import { useState, useEffect, useRef } from 'react'
import { 
  Play, Download, FileText, Copy, RefreshCw, Save, 
  ChevronDown, ChevronUp, AlertCircle, CheckCircle, 
  FileCode, Loader2, Sparkles
} from 'lucide-react'
import { jiraApi, llmApi, generatorApi, settingsApi, historyApi } from '../api/client'

const FOCUS_AREAS = [
  { id: 'functional', label: 'Functional Testing' },
  { id: 'performance', label: 'Performance Testing' },
  { id: 'security', label: 'Security Testing' },
  { id: 'automation', label: 'Automation Strategy' },
  { id: 'api', label: 'API Testing' },
  { id: 'accessibility', label: 'Accessibility Testing' },
  { id: 'disaster_recovery', label: 'Disaster Recovery' },
  { id: 'data_migration', label: 'Data Migration' },
  { id: 'mobile', label: 'Mobile Testing' },
]

const PROVIDER_MODELS = {
  groq: [
    'llama-3.3-70b-versatile',
    'llama-3.1-8b-instant',
    'deepseek-r1-distill-llama-70b',
    'qwen-qwq-32b',
  ],
  ollama: []
}

export default function Generator() {
  // Form state
  const [ticketInput, setTicketInput] = useState('')
  const [fetchChildren, setFetchChildren] = useState(true)
  const [additionalContext, setAdditionalContext] = useState('')
  const [provider, setProvider] = useState('groq')
  const [model, setModel] = useState('llama-3.3-70b-versatile')
  const [depth, setDepth] = useState('detailed')
  const [focusAreas, setFocusAreas] = useState(['functional', 'performance', 'security', 'automation', 'api'])
  const [temperature, setTemperature] = useState(0.3)
  
  // UI state
  const [loading, setLoading] = useState(false)
  const [fetching, setFetching] = useState(false)
  const [error, setError] = useState(null)
  const [jiraData, setJiraData] = useState(null)
  const [generatedContent, setGeneratedContent] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [stage, setStage] = useState(0)
  const [showPreview, setShowPreview] = useState(false)
  const [ollamaModels, setOllamaModels] = useState([])
  const contentRef = useRef('')

  // Load settings on mount
  useEffect(() => {
    loadSettings()
  }, [])

  // Load Ollama models when provider changes
  useEffect(() => {
    if (provider === 'ollama') {
      loadOllamaModels()
    }
  }, [provider])

  const loadSettings = async () => {
    try {
      const res = await settingsApi.get()
      const settings = res.data
      setProvider(settings.default_provider || 'groq')
      setModel(settings.groq_default_model || 'llama-3.3-70b-versatile')
      setDepth(settings.default_depth || 'detailed')
      setTemperature(settings.llm_temperature || 0.3)
    } catch (e) {
      console.error('Failed to load settings:', e)
    }
  }

  const loadOllamaModels = async () => {
    try {
      const res = await llmApi.getModels('ollama')
      setOllamaModels(res.data.models)
      if (res.data.models.length > 0) {
        setModel(res.data.models[0])
      }
    } catch (e) {
      console.error('Failed to load Ollama models:', e)
    }
  }

  const parseTicketIds = (input) => {
    return input
      .split(/[,\s]+/)
      .map(id => id.trim().toUpperCase())
      .filter(id => id && /^[A-Z]+-\d+$/.test(id))
  }

  const handleFetch = async () => {
    const ticketIds = parseTicketIds(ticketInput)
    if (ticketIds.length === 0) {
      setError('Please enter valid JIRA ticket IDs (e.g., VMO-1, VMO-2)')
      return
    }

    setFetching(true)
    setError(null)
    
    try {
      const res = await jiraApi.aggregate(ticketIds, fetchChildren)
      setJiraData(res.data)
      setShowPreview(true)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to fetch JIRA tickets')
    } finally {
      setFetching(false)
    }
  }

  const handleGenerate = async () => {
    const ticketIds = parseTicketIds(ticketInput)
    if (ticketIds.length === 0) {
      setError('Please enter valid JIRA ticket IDs')
      return
    }

    setLoading(true)
    setStreaming(true)
    setError(null)
    setGeneratedContent('')
    contentRef.current = ''
    setStage(1)

    try {
      await generatorApi.streamGenerate({
        jira_ticket_ids: ticketIds,
        fetch_children: fetchChildren,
        additional_context: additionalContext,
        provider: provider,
        model: model,
        depth: depth,
        focus_areas: focusAreas,
        temperature: temperature,
      }, (event) => {
        if (event.type === 'status') {
          setStage(event.stage)
        } else if (event.type === 'content') {
          contentRef.current += event.text
          setGeneratedContent(contentRef.current)
        } else if (event.type === 'done') {
          setStreaming(false)
          setLoading(false)
          setStage(0)
        } else if (event.type === 'error') {
          setError(event.error)
          setStreaming(false)
          setLoading(false)
        } else if (event.type === 'warning') {
          console.warn(event.message)
        }
      })
    } catch (e) {
      setError(e.message || 'Generation failed')
      setStreaming(false)
      setLoading(false)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedContent)
  }

  const handleExportPDF = async () => {
    try {
      const res = await generatorApi.exportPDF({
        content: generatedContent,
        title: 'Test Strategy',
        classification: 'Confidential',
      })
      const blob = new Blob([res.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'test-strategy.pdf'
      a.click()
    } catch (e) {
      setError('PDF export failed')
    }
  }

  const handleExportDOCX = async () => {
    try {
      const res = await generatorApi.exportDOCX({
        content: generatedContent,
        title: 'Test Strategy',
        classification: 'Confidential',
      })
      const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'test-strategy.docx'
      a.click()
    } catch (e) {
      setError('DOCX export failed')
    }
  }

  const handleSave = async () => {
    try {
      await historyApi.save({
        title: `Test Strategy - ${new Date().toLocaleDateString()}`,
        jira_ids: parseTicketIds(ticketInput).join(','),
        provider,
        model,
        depth,
        focus_areas: JSON.stringify(focusAreas),
        temperature,
        content: generatedContent,
      })
      alert('Saved to history!')
    } catch (e) {
      setError('Failed to save')
    }
  }

  const toggleFocusArea = (area) => {
    setFocusAreas(prev => 
      prev.includes(area) 
        ? prev.filter(a => a !== area)
        : [...prev, area]
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Strategy Generator</h1>
        <p className="text-gray-600">Generate comprehensive test strategies from JIRA tickets</p>
      </header>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-700">
          <AlertCircle className="w-5 h-5" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto text-sm underline">Dismiss</button>
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Left panel - Input */}
        <div className="space-y-6">
          {/* LLM Provider */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary-500" />
              LLM Configuration
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Provider</label>
                <div className="flex gap-2">
                  {['groq', 'ollama'].map(p => (
                    <button
                      key={p}
                      onClick={() => setProvider(p)}
                      className={`px-4 py-2 rounded-lg border capitalize transition-colors ${
                        provider === p 
                          ? 'bg-primary-500 text-white border-primary-500' 
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Model</label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  {provider === 'groq' ? (
                    PROVIDER_MODELS.groq.map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))
                  ) : (
                    ollamaModels.map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))
                  )}
                </select>
              </div>
            </div>
          </div>

          {/* JIRA Input */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h2 className="text-lg font-semibold mb-4">JIRA Tickets</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ticket IDs (comma or space separated)
                </label>
                <textarea
                  value={ticketInput}
                  onChange={(e) => setTicketInput(e.target.value)}
                  placeholder="e.g., VMO-1, VMO-2, VMO-15"
                  className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  rows={3}
                />
              </div>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={fetchChildren}
                  onChange={(e) => setFetchChildren(e.target.checked)}
                  className="w-4 h-4 text-primary-600 rounded"
                />
                <span className="text-sm text-gray-700">Fetch linked issues and subtasks</span>
              </label>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Additional Context (optional)
                </label>
                <textarea
                  value={additionalContext}
                  onChange={(e) => setAdditionalContext(e.target.value)}
                  placeholder="Add project-specific context: tech stack, compliance requirements, team structure..."
                  className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  rows={3}
                />
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleFetch}
                  disabled={fetching || !ticketInput.trim()}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {fetching ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
                  Fetch Only
                </button>
                <button
                  onClick={handleGenerate}
                  disabled={loading || !ticketInput.trim()}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                  {streaming ? 'Generating...' : 'Fetch & Generate'}
                </button>
              </div>
            </div>
          </div>

          {/* Generation Controls */}
          {jiraData && (
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h2 className="text-lg font-semibold mb-4">Generation Settings</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Strategy Depth</label>
                  <div className="flex gap-2">
                    {['standard', 'detailed', 'comprehensive'].map(d => (
                      <button
                        key={d}
                        onClick={() => setDepth(d)}
                        className={`px-4 py-2 rounded-lg border capitalize text-sm transition-colors ${
                          depth === d 
                            ? 'bg-primary-500 text-white border-primary-500' 
                            : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        {d}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Temperature: {temperature}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Focus Areas</label>
                  <div className="flex flex-wrap gap-2">
                    {FOCUS_AREAS.map(area => (
                      <button
                        key={area.id}
                        onClick={() => toggleFocusArea(area.id)}
                        className={`px-3 py-1 rounded-full text-sm border transition-colors ${
                          focusAreas.includes(area.id)
                            ? 'bg-primary-100 text-primary-700 border-primary-300'
                            : 'bg-gray-100 text-gray-600 border-gray-200 hover:bg-gray-200'
                        }`}
                      >
                        {focusAreas.includes(area.id) ? '☑' : '☐'} {area.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* JIRA Preview */}
          {jiraData && showPreview && (
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">JIRA Context Preview</h2>
                <button onClick={() => setShowPreview(!showPreview)}>
                  {showPreview ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </button>
              </div>
              
              {showPreview && (
                <div className="space-y-3 text-sm">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p><strong>Total Tickets:</strong> {jiraData.aggregated_context?.project_summary?.total_tickets}</p>
                    <p><strong>Epics:</strong> {jiraData.aggregated_context?.project_summary?.epics?.join(', ') || 'None'}</p>
                    <p><strong>Issue Types:</strong> {JSON.stringify(jiraData.aggregated_context?.project_summary?.issue_type_breakdown)}</p>
                  </div>
                  
                  {jiraData.errors?.length > 0 && (
                    <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800">
                      <p className="font-medium">Warnings:</p>
                      <ul className="list-disc list-inside">
                        {jiraData.errors.slice(0, 3).map((err, i) => (
                          <li key={i}>{err}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right panel - Output */}
        <div className="space-y-4">
          {/* Progress */}
          {streaming && (
            <div className="bg-white p-4 rounded-lg shadow-sm border">
              <div className="flex items-center gap-3 mb-3">
                <Loader2 className="w-5 h-5 animate-spin text-primary-500" />
                <span className="font-medium">Generating Test Strategy...</span>
              </div>
              <div className="space-y-2">
                {[
                  { num: 1, label: 'Analyzing JIRA context' },
                  { num: 2, label: 'Parsing template structure' },
                  { num: 3, label: 'Generating content' },
                  { num: 4, label: 'Finalizing document' },
                ].map(s => (
                  <div key={s.num} className="flex items-center gap-2 text-sm">
                    {stage > s.num ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : stage === s.num ? (
                      <div className="w-4 h-4 rounded-full border-2 border-primary-500 border-t-transparent animate-spin" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border-2 border-gray-300" />
                    )}
                    <span className={stage >= s.num ? 'text-gray-900' : 'text-gray-400'}>
                      {s.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Generated Content */}
          {generatedContent && (
            <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
              <div className="flex items-center justify-between p-4 border-b bg-gray-50">
                <h3 className="font-semibold flex items-center gap-2">
                  <FileCode className="w-5 h-5 text-primary-500" />
                  Generated Strategy
                </h3>
                <div className="flex gap-2">
                  <button
                    onClick={handleCopy}
                    className="p-2 hover:bg-gray-200 rounded-lg"
                    title="Copy to clipboard"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  <button
                    onClick={handleExportPDF}
                    className="p-2 hover:bg-gray-200 rounded-lg"
                    title="Download PDF"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                  <button
                    onClick={handleGenerate}
                    disabled={streaming}
                    className="p-2 hover:bg-gray-200 rounded-lg disabled:opacity-50"
                    title="Regenerate"
                  >
                    <RefreshCw className={`w-4 h-4 ${streaming ? 'animate-spin' : ''}`} />
                  </button>
                </div>
              </div>
              
              <div className="p-6 max-h-[600px] overflow-auto">
                <div className="document-preview prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-gray-800">
                    {generatedContent}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {!generatedContent && !streaming && (
            <div className="bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
              <Sparkles className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">Enter JIRA tickets and click Generate to create a test strategy</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
