import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { getConversations, deleteConversation } from '../services/api'
import type { Conversation } from '../types'

export default function Conversations() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    getConversations()
      .then(res => setConversations(res.conversations))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await deleteConversation(id)
      setConversations(prev => prev.filter(c => c.id !== id))
    } catch { /* ignore */ }
  }

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
      })
    } catch { return dateStr }
  }

  return (
    <div className="conversations-page">
      <h2>Conversation History</h2>

      {loading ? (
        <div className="loading-state">Loading...</div>
      ) : conversations.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
          </div>
          <h3>No conversations yet</h3>
          <p className="text-dim">Start a chat to see your history here</p>
        </div>
      ) : (
        <motion.div className="conversation-list" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {conversations.map(conv => (
            <div key={conv.id} className="conversation-item" onClick={() => navigate('/')}>
              <div className="conv-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
              <div className="conv-info">
                <div className="conv-title">{conv.title}</div>
                <div className="conv-date">{formatDate(conv.created_at)}</div>
              </div>
              <button className="conv-delete" onClick={(e) => handleDelete(conv.id, e)}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                </svg>
              </button>
            </div>
          ))}
        </motion.div>
      )}

      <style>{`
        .conversations-page { max-width: 800px; margin: 0 auto; }
        .conversations-page h2 { margin-bottom: 20px; }
        .conversation-list { display: flex; flex-direction: column; gap: 8px; }
        .conversation-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 14px 16px;
          border-radius: 12px;
          background: var(--glass-card);
          border: 1px solid var(--glass-border);
          cursor: pointer;
          transition: var(--transition-smooth);
        }
        .conversation-item:hover { background: var(--glass-highlight); }
        .conv-icon { color: var(--primary); flex-shrink: 0; }
        .conv-info { flex: 1; min-width: 0; }
        .conv-title { font-weight: 600; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .conv-date { font-size: 0.8rem; color: var(--text-dim); margin-top: 4px; }
        .conv-delete { background: none; border: none; color: var(--text-dim); cursor: pointer; padding: 4px; border-radius: 4px; transition: var(--transition-smooth); }
        .conv-delete:hover { color: var(--danger); background: rgba(255,0,0,0.1); }
        .loading-state, .empty-state { text-align: center; padding: 60px 20px; color: var(--text-dim); }
        .empty-icon { color: var(--primary); opacity: 0.3; margin-bottom: 16px; }
      `}</style>
    </div>
  )
}
