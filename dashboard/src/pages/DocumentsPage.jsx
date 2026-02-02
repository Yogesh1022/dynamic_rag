import React, { useState, useEffect } from 'react'
import { Upload, FileText, Trash2, CheckCircle, Clock, AlertCircle, Loader2 } from 'lucide-react'
import { uploadDocument, listDocuments, deleteDocument } from '../api/client'
import './DocumentsPage.css'

function DocumentsPage() {
  const [documents, setDocuments] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      const docs = await listDocuments()
      setDocuments(docs)
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileSelect = async (files) => {
    if (!files || files.length === 0) return

    const file = files[0]
    setIsUploading(true)
    setUploadProgress(0)

    try {
      await uploadDocument(file, (progress) => {
        setUploadProgress(progress)
      })
      
      // Wait a bit for processing to start
      setTimeout(() => {
        loadDocuments()
      }, 1000)
      
    } catch (error) {
      console.error('Upload failed:', error)
      alert(`Upload failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files)
    }
  }

  const handleDelete = async (docId) => {
    if (!confirm('Are you sure you want to delete this document?')) return

    try {
      await deleteDocument(docId)
      loadDocuments()
    } catch (error) {
      console.error('Delete failed:', error)
      alert(`Delete failed: ${error.response?.data?.detail || error.message}`)
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={16} className="status-icon success" />
      case 'processing':
        return <Clock size={16} className="status-icon processing" />
      case 'failed':
        return <AlertCircle size={16} className="status-icon error" />
      default:
        return <Clock size={16} className="status-icon" />
    }
  }

  return (
    <div className="documents-page">
      <div className="page-header">
        <div>
          <h1>Document Management</h1>
          <p className="subtitle">Upload and manage your documents for RAG</p>
        </div>
        <button className="btn-primary" onClick={() => document.getElementById('file-input').click()}>
          <Upload size={20} />
          Upload Document
        </button>
      </div>

      <div 
        className={`upload-area ${dragActive ? 'drag-active' : ''} ${isUploading ? 'uploading' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !isUploading && document.getElementById('file-input').click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.tiff"
          onChange={(e) => handleFileSelect(e.target.files)}
          style={{ display: 'none' }}
        />
        
        {isUploading ? (
          <div className="upload-progress">
            <Loader2 className="spin" size={48} />
            <p>Uploading... {uploadProgress}%</p>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
            </div>
          </div>
        ) : (
          <>
            <Upload size={48} className="upload-icon" />
            <p className="upload-text">Drag and drop files here or click to browse</p>
            <p className="upload-hint">Supported: PDF, PNG, JPG, JPEG, TIFF (max 10MB)</p>
          </>
        )}
      </div>

      <div className="documents-list">
        <h2>Documents ({documents.length})</h2>
        
        {isLoading ? (
          <div className="loading-state">
            <Loader2 className="spin" size={32} />
            <p>Loading documents...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="empty-state">
            <FileText size={64} />
            <p>No documents uploaded yet</p>
            <p className="empty-hint">Upload a document to get started with RAG</p>
          </div>
        ) : (
          <div className="documents-grid">
            {documents.map((doc) => (
              <div key={doc.id} className="document-card fade-in">
                <div className="document-header">
                  <FileText size={24} className="document-icon" />
                  <button 
                    className="delete-btn"
                    onClick={() => handleDelete(doc.id)}
                    title="Delete document"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
                
                <div className="document-body">
                  <h3 className="document-name" title={doc.filename}>
                    {doc.filename}
                  </h3>
                  
                  <div className="document-meta">
                    <div className="meta-item">
                      {getStatusIcon(doc.status)}
                      <span className={`status-text ${doc.status}`}>
                        {doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
                      </span>
                    </div>
                    
                    <div className="meta-item">
                      <span>{formatFileSize(doc.file_size)}</span>
                    </div>
                    
                    {doc.total_chunks > 0 && (
                      <div className="meta-item">
                        <span>{doc.total_chunks} chunks</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="document-footer">
                    <span className="upload-date" title={formatDate(doc.created_at)}>
                      {new Date(doc.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default DocumentsPage
