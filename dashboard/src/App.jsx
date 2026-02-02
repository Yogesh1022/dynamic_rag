import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { MessageSquare, Upload, History, BarChart3, Menu, X } from 'lucide-react'
import ChatPage from './pages/ChatPage'
import DocumentsPage from './pages/DocumentsPage'
import ConversationsPage from './pages/ConversationsPage'
import DashboardPage from './pages/DashboardPage'
import './App.css'

function Navigation() {
  const location = useLocation()
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  
  const navItems = [
    { path: '/', icon: MessageSquare, label: 'Chat' },
    { path: '/documents', icon: Upload, label: 'Documents' },
    { path: '/conversations', icon: History, label: 'History' },
    { path: '/dashboard', icon: BarChart3, label: 'Dashboard' },
  ]
  
  return (
    <nav className="navbar">
      <div className="nav-container">
        <div className="nav-brand">
          <MessageSquare size={24} />
          <span>RAG Dashboard</span>
          <span className="model-badge">Llama3</span>
        </div>
        
        <button 
          className="menu-toggle"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
        >
          {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
        
        <div className={`nav-links ${isMenuOpen ? 'open' : ''}`}>
          {navItems.map(({ path, icon: Icon, label }) => (
            <Link
              key={path}
              to={path}
              className={`nav-link ${location.pathname === path ? 'active' : ''}`}
              onClick={() => setIsMenuOpen(false)}
            >
              <Icon size={20} />
              <span>{label}</span>
            </Link>
          ))}
        </div>
      </div>
    </nav>
  )
}

function App() {
  return (
    <Router>
      <div className="app">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/conversations" element={<ConversationsPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
