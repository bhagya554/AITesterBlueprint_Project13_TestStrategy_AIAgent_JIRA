import { useState, useEffect } from 'react'
import { Save, CheckCircle, AlertCircle, Upload, Eye, EyeOff, TestTube } from 'lucide-react'
import { settingsApi, jiraApi, llmApi, templateApi } from '../api/client'

export default function Settings() {
  const [settings, setSettings] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [showSecrets, setShowSecrets] = useState({})
  const [testResults, setTestResults] = useState({})

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const res = await settingsApi.get()
      setSettings(res.data)
    } catch (e) {
      setMessage({ type: 'error', text: 'Failed to load settings' })
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await settingsApi.update(settings)
      setMessage({ type: 'success', text: 'Settings saved successfully' })
    } catch (e) {
      setMessage({ type: 'error', text: 'Failed to save settings' })
    } finally {
      setSaving(false)
    }
  }

  const handleChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  const toggleSecret = (key) => {
    setShowSecrets(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const testJira = async () => {
    setTestResults(prev => ({ ...prev, jira: { loading: true } }))
    try {
      const res = await jiraApi.testConnection()
      setTestResults(prev => ({ 
        ...prev, 
        jira: { success: true, message: `Connected as ${res.data.display_name}` }
      }))
    } catch (e) {
      setTestResults(prev => ({ 
        ...prev, 
        jira: { success: false, message: e.response?.data?.detail || 'Connection failed' }
      }))
    }
  }

  const testLLM = async (provider) => {
    setTestResults(prev => ({ ...prev, [provider]: { loading: true } }))
    try {
      const res = await llmApi.testConnection(provider)
      setTestResults(prev => ({ 
        ...prev, 
        [provider]: { success: true, message: res.data.connection_test?.message || 'Connected' }
      }))
    } catch (e) {
      setTestResults(prev => ({ 
        ...prev, 
        [provider]: { success: false, message: e.response?.data?.detail || 'Connection failed' }
      }))
    }
  }

  const handleTemplateUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      await templateApi.upload(file)
      setMessage({ type: 'success', text: 'Template uploaded successfully' })
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to upload template' })
    }
  }

  if (loading) return <div className="p-6">Loading...</div>

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Configure JIRA, LLM providers, and application preferences</p>
      </header>

      {message && (
        <div className={`mb-6 p-4 rounded-lg flex items-center gap-3 ${
          message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {message.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
          {message.text}
          <button onClick={() => setMessage(null)} className="ml-auto text-sm underline">Dismiss</button>
        </div>
      )}

      <div className="space-y-6">
        {/* JIRA Settings */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-lg font-semibold mb-4">JIRA Configuration</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
              <input
                type="url"
                value={settings.jira_base_url || ''}
                onChange={(e) => handleChange('jira_base_url', e.target.value)}
                placeholder="https://your-domain.atlassian.net"
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={settings.jira_email || ''}
                onChange={(e) => handleChange('jira_email', e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Token</label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type={showSecrets.jira ? 'text' : 'password'}
                    value={settings.jira_api_token || ''}
                    onChange={(e) => handleChange('jira_api_token', e.target.value)}
                    placeholder={settings.jira_api_token_set ? '••••••••••••' : ''}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                  <button
                    onClick={() => toggleSecret('jira')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showSecrets.jira ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <button
                  onClick={testJira}
                  disabled={testResults.jira?.loading}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2 disabled:opacity-50"
                >
                  <TestTube className="w-4 h-4" />
                  Test
                </button>
              </div>
              {testResults.jira && !testResults.jira.loading && (
                <p className={`mt-1 text-sm ${testResults.jira.success ? 'text-green-600' : 'text-red-600'}`}>
                  {testResults.jira.message}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Groq Settings */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-lg font-semibold mb-4">Groq Configuration</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type={showSecrets.groq ? 'text' : 'password'}
                    value={settings.groq_api_key || ''}
                    onChange={(e) => handleChange('groq_api_key', e.target.value)}
                    placeholder={settings.groq_api_key_set ? '••••••••••••' : ''}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                  <button
                    onClick={() => toggleSecret('groq')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showSecrets.groq ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <button
                  onClick={() => testLLM('groq')}
                  disabled={testResults.groq?.loading}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2 disabled:opacity-50"
                >
                  <TestTube className="w-4 h-4" />
                  Test
                </button>
              </div>
              {testResults.groq && !testResults.groq.loading && (
                <p className={`mt-1 text-sm ${testResults.groq.success ? 'text-green-600' : 'text-red-600'}`}>
                  {testResults.groq.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Default Model</label>
              <select
                value={settings.groq_default_model || 'llama-3.3-70b-versatile'}
                onChange={(e) => handleChange('groq_default_model', e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile</option>
                <option value="llama-3.1-8b-instant">llama-3.1-8b-instant</option>
                <option value="deepseek-r1-distill-llama-70b">deepseek-r1-distill-llama-70b</option>
                <option value="qwen-qwq-32b">qwen-qwq-32b</option>
              </select>
            </div>
          </div>
        </div>

        {/* Ollama Settings */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-lg font-semibold mb-4">Ollama Configuration</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
              <div className="flex gap-2">
                <input
                  type="url"
                  value={settings.ollama_base_url || 'http://localhost:11434'}
                  onChange={(e) => handleChange('ollama_base_url', e.target.value)}
                  className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                />
                <button
                  onClick={() => testLLM('ollama')}
                  disabled={testResults.ollama?.loading}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2 disabled:opacity-50"
                >
                  <TestTube className="w-4 h-4" />
                  Test
                </button>
              </div>
              {testResults.ollama && !testResults.ollama.loading && (
                <p className={`mt-1 text-sm ${testResults.ollama.success ? 'text-green-600' : 'text-red-600'}`}>
                  {testResults.ollama.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Default Model</label>
              <input
                type="text"
                value={settings.ollama_default_model || 'llama3.1'}
                onChange={(e) => handleChange('ollama_default_model', e.target.value)}
                placeholder="llama3.1"
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>
        </div>

        {/* Template Settings */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-lg font-semibold mb-4">Template Configuration</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Upload New Template (PDF)</label>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50 cursor-pointer">
                  <Upload className="w-4 h-4" />
                  Choose File
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleTemplateUpload}
                    className="hidden"
                  />
                </label>
                <span className="text-sm text-gray-500">teststrategy.pdf</span>
              </div>
            </div>
          </div>
        </div>

        {/* Default Settings */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-lg font-semibold mb-4">Default Generation Settings</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Default Depth</label>
              <select
                value={settings.default_depth || 'detailed'}
                onChange={(e) => handleChange('default_depth', e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                <option value="standard">Standard</option>
                <option value="detailed">Detailed</option>
                <option value="comprehensive">Comprehensive</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Default Temperature: {settings.llm_temperature || 0.3}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.llm_temperature || 0.3}
                onChange={(e) => handleChange('llm_temperature', parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
          >
            {saving ? 'Saving...' : <><Save className="w-4 h-4" /> Save Settings</>}
          </button>
        </div>
      </div>
    </div>
  )
}
