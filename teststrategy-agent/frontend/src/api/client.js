import axios from 'axios'

// Use environment variable for API URL, fallback to relative path
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// JIRA API
export const jiraApi = {
  getTicket: (ticketId, fetchChildren = true) => 
    api.get(`/jira/ticket/${ticketId}?fetch_children_flag=${fetchChildren}`),
  
  getTickets: (ticketIds, fetchChildren = true) => 
    api.post('/jira/tickets', { ticket_ids: ticketIds, fetch_children: fetchChildren }),
  
  getChildren: (ticketId) => 
    api.get(`/jira/ticket/${ticketId}/children`),
  
  testConnection: () => 
    api.get('/jira/test-connection'),
  
  aggregate: (ticketIds, fetchChildren = true) => 
    api.post('/jira/aggregate', { ticket_ids: ticketIds, fetch_children: fetchChildren }),
}

// LLM API
export const llmApi = {
  getProviders: () => 
    api.get('/llm/providers'),
  
  getModels: (provider) => 
    api.get(`/llm/models/${provider}`),
  
  testConnection: (provider, model = null) => 
    api.post('/llm/test', { provider, model }),
}

// Template API
export const templateApi = {
  preview: () => 
    api.get('/template/preview'),
  
  upload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/template/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  getCurrent: () => 
    api.get('/template/current'),
}

// Settings API
export const settingsApi = {
  get: () => 
    api.get('/settings'),
  
  update: (updates) => 
    api.put('/settings', updates),
  
  getDefaults: () => 
    api.get('/settings/defaults'),
}

// History API
export const historyApi = {
  list: (params = {}) => 
    api.get('/history', { params }),
  
  get: (id) => 
    api.get(`/history/${id}`),
  
  delete: (id) => 
    api.delete(`/history/${id}`),
  
  clone: (id) => 
    api.post(`/history/${id}/clone`),
}

// Generator API - Uses fetch for SSE streaming
export const generatorApi = {
  streamGenerate: async (requestBody, onEvent) => {
    const baseUrl = import.meta.env.VITE_API_URL || ''
    const response = await fetch(`${baseUrl}/api/generate/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    })
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const text = decoder.decode(value)
      const lines = text.split('\n').filter(line => line.trim())
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            onEvent(data)
          } catch (e) {
            console.error('Failed to parse SSE data:', line)
          }
        }
      }
    }
  },
  
  regenerateSection: (request) => 
    api.post('/generate/section', request),
  
  exportPDF: (request) => 
    api.post('/generate/export/pdf', request, { responseType: 'blob' }),
  
  exportDOCX: (request) => 
    api.post('/generate/export/docx', request, { responseType: 'blob' }),
}

export default api
