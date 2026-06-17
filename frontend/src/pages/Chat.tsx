import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import ChatMessage from '../components/ChatMessage'
import { sendChat, getConversationMessages, getDocuments } from '../services/api'
import type { Message, Document } from '../types'

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([])
  const [showDocs, setShowDocs] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getDocuments().then(res => setDocuments(res.documents)).catch(() => {})
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return
    const msg = input.trim()
    setInput('')

    const userMsg: Message = {
      id: Date.now().toString(),
      conversation_id: conversationId || '',
      role: 'user',
      content: msg,
      sources: [],
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const res = await sendChat({
        conversation_id: conversationId || undefined,
        message: msg,
        document_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
      })
      setConversationId(res.conversation_id)
      const assistantMsg: Message = {
        id: Date.now().toString() + '-a',
        conversation_id: res.conversation_id,
        role: 'assistant',
        content: res.message,
        sources: res.sources,
        created_at: new Date().toISOString(),
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now().toString() + '-e',
        conversation_id: conversationId || '',
        role: 'assistant',
        content: 'Error sending message. Make sure the backend is running.',
        sources: [],
        created_at: new Date().toISOString(),
      }])
    }
    setLoading(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const newChat = () => {
    setMessages([])
    setConversationId(null)
    setInput('')
  }

  return (
    <div className="chat-page">
      <div className="chat-header">
        <h2>Chat with your Documents</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost" onClick={() => setShowDocs(!showDocs)}>
            {showDocs ? 'Hide' : 'Filter'} Docs ({selectedDocIds.length})
          </button>
          <button className="btn btn-ghost" onClick={newChat}>New Chat</button>
        </div>
      </div>

      {showDocs && (
        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="doc-filter">
          <p className="text-dim" style={{ fontSize: '0.85rem', marginBottom: 8 }}>Select documents to search within:</p>
          <div className="doc-filter-list">
            {documents.filter(d => d.status === 'processed').map(doc => (
              <button
                key={doc.id}
                className={`doc-chip ${selectedDocIds.includes(doc.id) ? 'active' : ''}`}
                onClick={() => setSelectedDocIds(prev =>
                  prev.includes(doc.id) ? prev.filter(id => id !== doc.id) : [...prev, doc.id]
                )}
              >
                {doc.filename}
              </button>
            ))}
            {documents.filter(d => d.status === 'processed').length === 0 && (
              <span className="text-dim" style={{ fontSize: '0.85rem' }}>No processed documents yet</span>
            )}
          </div>
        </motion.div>
      )}

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-welcome">
            <div className="welcome-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <h3>Ask anything about your documents</h3>
            <p className="text-dim">Upload documents first, then ask questions to get AI-powered answers</p>
          </div>
        )}
        {messages.map(msg => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        {loading && (
          <div className="message assistant" style={{ alignSelf: 'flex-start' }}>
            <div className="typing-indicator"><span /><span /><span /></div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-bar">
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your documents..."
          rows={1}
          className="chat-input"
        />
        <button className="btn btn-primary send-btn" onClick={handleSend} disabled={loading || !input.trim()}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>

      <style>{`
        .chat-page { display: flex; flex-direction: column; height: calc(100vh - 100px); }
        .chat-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
        .chat-header h2 { margin: 0; }
        .btn-ghost { background: var(--glass-card); border: 1px solid var(--glass-border); color: var(--text); padding: 8px 16px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; transition: var(--transition-smooth); }
        .btn-ghost:hover { background: var(--glass-highlight); }
        .doc-filter { padding: 12px; margin-bottom: 12px; border-radius: 12px; background: var(--glass-card); border: 1px solid var(--glass-border); overflow: hidden; }
        .doc-filter-list { display: flex; flex-wrap: wrap; gap: 8px; }
        .doc-chip { padding: 6px 12px; border-radius: 20px; border: 1px solid var(--glass-border); background: transparent; color: var(--text-dim); cursor: pointer; font-size: 0.8rem; transition: var(--transition-smooth); }
        .doc-chip.active { border-color: var(--primary); background: var(--primary-glow); color: var(--primary); }
        .chat-messages { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; padding: 16px 0; }
        .chat-welcome { text-align: center; margin: auto; max-width: 400px; }
        .welcome-icon { color: var(--primary); opacity: 0.5; margin-bottom: 16px; }
        .typing-indicator { display: flex; gap: 4px; padding: 12px 16px; background: var(--glass-card); border-radius: 16px; border: 1px solid var(--glass-border); }
        .typing-indicator span { width: 8px; height: 8px; border-radius: 50%; background: var(--text-dim); animation: bounce 1.4s infinite ease-in-out; }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        .chat-input-bar { display: flex; gap: 8px; padding: 12px 0; border-top: 1px solid var(--glass-border); margin-top: 12px; }
        .chat-input {
          flex: 1;
          padding: 12px 16px;
          border-radius: 12px;
          border: 1px solid var(--glass-border);
          background: var(--glass-card);
          color: var(--text);
          font-size: 0.95rem;
          resize: none;
          transition: var(--transition-smooth);
          font-family: inherit;
        }
        .chat-input:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-glow); }
        .send-btn { padding: 12px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
        .send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
      `}</style>
    </div>
  )
}
