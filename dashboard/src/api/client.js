import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_KEY = import.meta.env.VITE_API_KEY || 'your-secret-api-key-change-in-production'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
})

// Health check
export const checkHealth = async () => {
  const response = await apiClient.get('/health')
  return response.data
}

// Chat
export const sendChatMessage = async (query, conversationId = null, options = {}) => {
  const response = await apiClient.post('/api/v1/chat', {
    query,
    conversation_id: conversationId,
    model: options.model || 'llama3',
    temperature: options.temperature || 0.7,
    top_k: options.top_k || 5,
    use_hybrid: options.use_hybrid !== undefined ? options.use_hybrid : true,
  })
  return response.data
}

// Documents
export const uploadDocument = async (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await apiClient.post('/api/v1/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percentCompleted)
      }
    },
  })
  return response.data
}

export const listDocuments = async () => {
  const response = await apiClient.get('/api/v1/documents/')
  return response.data
}

export const deleteDocument = async (documentId) => {
  const response = await apiClient.delete(`/api/v1/documents/${documentId}`)
  return response.data
}

export default apiClient
