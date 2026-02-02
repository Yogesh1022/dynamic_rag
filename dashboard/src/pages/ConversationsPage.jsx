import React from 'react'
import { MessageSquare, Calendar } from 'lucide-react'
import './ConversationsPage.css'

function ConversationsPage() {
  // Placeholder - in production this would fetch from backend
  const conversations = []

  return (
    <div className="conversations-page">
      <div className="page-header">
        <div>
          <h1>Conversation History</h1>
          <p className="subtitle">Browse your previous chat sessions</p>
        </div>
      </div>

      <div className="conversations-container">
        {conversations.length === 0 ? (
          <div className="empty-state">
            <MessageSquare size={64} />
            <p>No conversation history yet</p>
            <p className="empty-hint">Start chatting to see your conversations here</p>
          </div>
        ) : (
          <div className="conversations-list">
            {conversations.map((conv) => (
              <div key={conv.id} className="conversation-card">
                <div className="conversation-header">
                  <MessageSquare size={20} />
                  <h3>{conv.title}</h3>
                </div>
                <div className="conversation-meta">
                  <Calendar size={14} />
                  <span>{new Date(conv.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ConversationsPage
