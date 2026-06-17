import { useState, useRef, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import ChatMessage from '../components/ChatMessage'
import { getDocuments, sendChat } from '../services/api'
import type { Message, Document, Source } from '../types'

const API_BASE = 'http://localhost:8000/api'

function getToken(): string | null {
  return localStorage.getItem('access_token')
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([])
  const [showDocs, setShowDocs] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    getDocuments().then(res => setDocuments(res.documents)).catch(() => {})
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = useCallback(async () => {
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

    const assistantId = (Date.now() + 1).toString()
    const assistantMsg: Message = {
      id: assistantId,
      conversation_id: conversationId || '',
      role: 'assistant',
      content: '',
      sources: [],
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, assistantMsg])

    const body = JSON.stringify({
      conversation_id: conversationId || undefined,
      message: msg,
      document_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
    })

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`,
        },
        body,
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No reader')

      const decoder = new TextDecoder()
      let buffer = ''
      let sources: Source[] = []
      let fullContent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue
          try {
            const data = JSON.parse(line)
            if (data.type === 'token') {
              fullContent += data.content
              setMessages(prev => prev.map(m =>
                m.id === assistantId ? { ...m, content: fullContent } : m
              ))
            } else if (data.type === 'done') {
              sources = data.sources || []
              setMessages(prev => prev.map(m =>
                m.id === assistantId ? { ...m, sources, content: fullContent } : m
              ))
              if (data.conversation_id) {
                setConversationId(data.conversation_id)
              }
            }
          } catch { /* ignore parse errors */ }
        }
      }

      if (!fullContent) {
        const fallbackRes = await sendChat({
          conversation_id: conversationId || undefined,
          message: msg,
          document_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
        })
        setConversationId(fallbackRes.conversation_id)
        setMessages(prev => prev.map(m =>
          m.id === assistantId ? { ...m, content: fallbackRes.message, sources: fallbackRes.sources } : m
        ))
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') return
      try {
        const fallbackRes = await sendChat({
          conversation_id: conversationId || undefined,
          message: msg,
          document_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
        })
        setConversationId(fallbackRes.conversation_id)
        setMessages(prev => prev.map(m =>
          m.id === assistantId ? { ...m, content: fallbackRes.message, sources: fallbackRes.sources } : m
        ))
      } catch {
        setMessages(prev => prev.map(m =>
          m.id === assistantId ? { ...m, content: 'Error sending message. Make sure the backend is running.' } : m
        ))
      }
    }
    setLoading(false)
    abortRef.current = null
  }, [input, loading, conversationId, selectedDocIds])

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
