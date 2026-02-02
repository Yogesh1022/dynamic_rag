import React, { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Settings, User, Bot, FileText, Clock } from 'lucide-react'
import { sendChatMessage } from '../api/client'
import './ChatPage.css'

function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const [showSettings, setShowSettings] = useState(false)
  const [settings, setSettings] = useState({
    model: 'llama3',
    temperature: 0.7,
    top_k: 5,
    use_hybrid: true,
  })
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Welcome message
    setMessages([
      {
        role: 'assistant',
        content: 'Hello! I\'m your RAG assistant powered by Llama3. Upload some documents and ask me questions about them!',
        timestamp: new Date().toISOString(),
      }
    ])
  }, [])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await sendChatMessage(input, conversationId, settings)
      
      if (!conversationId) {
        setConversationId(response.conversation_id)
      }

      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString(),
        sources: response.retrieved_documents,
        metadata: response.metadata,
        latency: response.latency_ms,
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      
      const errorMessage = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.response?.data?.detail || error.message}. Please make sure the backend server is running and Ollama is started.`,
        timestamp: new Date().toISOString(),
        isError: true,
      }
      
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleNewChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: 'Starting a new conversation. How can I help you?',
        timestamp: new Date().toISOString(),
      }
    ])
    setConversationId(null)
  }

  return (
    <div className="chat-page">
      <div className="chat-header">
        <div>
          <h1>Chat with Documents</h1>
          <p className="subtitle">
            Powered by Llama3 • 
            {conversationId ? ` Conversation: ${conversationId.slice(0, 8)}` : ' New conversation'}
          </p>
        </div>
        <div className="header-actions">
          <button className="btn-secondary" onClick={handleNewChat}>
            New Chat
          </button>
          <button 
            className={`btn-icon ${showSettings ? 'active' : ''}`}
            onClick={() => setShowSettings(!showSettings)}
            title="Settings"
          >
            <Settings size={20} />
          </button>
        </div>
      </div>

      {showSettings && (
        <div className="settings-panel fade-in">
          <h3>Chat Settings</h3>
          <div className="settings-grid">
            <div className="setting-item">
              <label>Model</label>
              <select 
                value={settings.model}
                onChange={(e) => setSettings({...settings, model: e.target.value})}
              >
                <option value="llama3">Llama3 (Recommended)</option>
                <option value="mistral">Mistral</option>
                <option value="codellama">Code Llama</option>
                <option value="gemma3:4b">Gemma3 4B</option>
              </select>
            </div>
            
            <div className="setting-item">
              <label>Temperature: {settings.temperature}</label>
              <input 
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.temperature}
                onChange={(e) => setSettings({...settings, temperature: parseFloat(e.target.value)})}
              />
            </div>
            
            <div className="setting-item">
              <label>Retrieved Chunks: {settings.top_k}</label>
              <input 
                type="range"
                min="1"
                max="10"
                step="1"
                value={settings.top_k}
                onChange={(e) => setSettings({...settings, top_k: parseInt(e.target.value)})}
              />
            </div>
            
            <div className="setting-item">
              <label className="checkbox-label">
                <input 
                  type="checkbox"
                  checked={settings.use_hybrid}
                  onChange={(e) => setSettings({...settings, use_hybrid: e.target.checked})}
                />
                <span>Use Hybrid Search (Vector + BM25)</span>
              </label>
            </div>
          </div>
        </div>
      )}

      <div className="messages-container">
        <div className="messages">
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.role} fade-in`}>
              <div className="message-avatar">
                {message.role === 'user' ? <User size={20} /> : <Bot size={20} />}
              </div>
              <div className="message-content">
                <div className={`message-bubble ${message.isError ? 'error' : ''}`}>
                  {message.content}
                </div>
                
                {message.sources && message.sources.length > 0 && (
                  <div className="message-sources">
                    <div className="sources-header">
                      <FileText size={14} />
                      <span>Sources ({message.sources.length})</span>
                    </div>
                    <div className="sources-list">
                      {message.sources.map((source, idx) => (
                        <div key={idx} className="source-item">
                          <div className="source-header">
                            <span className="source-title">
                              Document {source.source} • Page {source.page}
                            </span>
                            <span className="source-score">
                              Score: {source.score.toFixed(3)}
                            </span>
                          </div>
                          <div className="source-content">{source.content}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {message.latency && (
                  <div className="message-metadata">
                    <Clock size={12} />
                    <span>{message.latency.toFixed(0)}ms</span>
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="message assistant fade-in">
              <div className="message-avatar">
                <Bot size={20} />
              </div>
              <div className="message-content">
                <div className="message-bubble">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="input-container">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question about your documents..."
          rows="1"
          disabled={isLoading}
        />
        <button 
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          className="send-button"
        >
          {isLoading ? <Loader2 className="spin" size={20} /> : <Send size={20} />}
        </button>
      </div>
    </div>
  )
}

export default ChatPage
