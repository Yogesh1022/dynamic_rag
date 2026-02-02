import React, { useState, useEffect } from 'react'
import { Activity, FileText, MessageSquare, Zap, Server, Database } from 'lucide-react'
import { checkHealth, listDocuments } from '../api/client'
import './DashboardPage.css'

function DashboardPage() {
  const [health, setHealth] = useState(null)
  const [documents, setDocuments] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [healthData, docsData] = await Promise.all([
        checkHealth(),
        listDocuments()
      ])
      setHealth(healthData)
      setDocuments(docsData)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const stats = [
    {
      icon: FileText,
      label: 'Total Documents',
      value: documents.length,
      color: '#3b82f6'
    },
    {
      icon: MessageSquare,
      label: 'Total Chunks',
      value: documents.reduce((sum, doc) => sum + (doc.total_chunks || 0), 0),
      color: '#10b981'
    },
    {
      icon: Zap,
      label: 'Processed',
      value: documents.filter(d => d.status === 'completed').length,
      color: '#f59e0b'
    },
    {
      icon: Activity,
      label: 'Status',
      value: health?.status || 'Unknown',
      color: '#8b5cf6'
    }
  ]

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="subtitle">System overview and metrics</p>
        </div>
      </div>

      <div className="stats-grid">
        {stats.map((stat, index) => (
          <div key={index} className="stat-card fade-in" style={{ '--delay': `${index * 0.1}s` }}>
            <div className="stat-icon" style={{ background: stat.color }}>
              <stat.icon size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-value">{stat.value}</div>
              <div className="stat-label">{stat.label}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <div className="card-header">
            <Server size={20} />
            <h2>System Status</h2>
          </div>
          <div className="card-body">
            <div className="status-list">
              <div className="status-item">
                <span className="status-label">FastAPI</span>
                <span className={`status-badge ${health ? 'success' : 'error'}`}>
                  {health ? 'Healthy' : 'Offline'}
                </span>
              </div>
              <div className="status-item">
                <span className="status-label">Llama3 Model</span>
                <span className="status-badge success">Active</span>
              </div>
              <div className="status-item">
                <span className="status-label">Vector Search</span>
                <span className="status-badge success">Hybrid</span>
              </div>
            </div>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-header">
            <Database size={20} />
            <h2>Recent Documents</h2>
          </div>
          <div className="card-body">
            {documents.slice(0, 5).length > 0 ? (
              <div className="documents-preview">
                {documents.slice(0, 5).map((doc) => (
                  <div key={doc.id} className="preview-item">
                    <FileText size={16} />
                    <div className="preview-content">
                      <div className="preview-name">{doc.filename}</div>
                      <div className="preview-meta">
                        {doc.total_chunks} chunks • {doc.status}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-preview">
                <p>No documents uploaded yet</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="info-section">
        <h2>About This System</h2>
        <div className="info-grid">
          <div className="info-item">
            <strong>LLM Model:</strong>
            <span>Llama3 (Meta)</span>
          </div>
          <div className="info-item">
            <strong>Embedding Model:</strong>
            <span>nomic-embed-text (768-dim)</span>
          </div>
          <div className="info-item">
            <strong>Vector Database:</strong>
            <span>Qdrant</span>
          </div>
          <div className="info-item">
            <strong>Search Method:</strong>
            <span>Hybrid (Vector + BM25)</span>
          </div>
          <div className="info-item">
            <strong>Re-ranking:</strong>
            <span>Multi-signal scoring</span>
          </div>
          <div className="info-item">
            <strong>Backend:</strong>
            <span>FastAPI + Python</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
