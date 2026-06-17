import { motion } from 'framer-motion'
import type { Message } from '../types'

interface Props {
  message: Message
}

export default function ChatMessage({ message }: Props) {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`message ${isUser ? 'user' : 'assistant'}`}
    >
      <div className="message-avatar">
        {isUser ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
        )}
      </div>
      <div className="message-content">
        <div className="message-text">{message.content}</div>
        {message.sources && message.sources.length > 0 && (
          <div className="message-sources">
            <details>
              <summary>Sources ({message.sources.length})</summary>
              {message.sources.map((s, i) => (
                <div key={i} className="source-item">
                  <div className="source-name">{s.document_name}</div>
                  <div className="source-text">{s.content.substring(0, 200)}...</div>
                  <div className="source-score">Relevance: {s.relevance_score}</div>
                </div>
              ))}
            </details>
          </div>
        )}
      </div>

      <style>{`
        .message {
          display: flex;
          gap: 12px;
          max-width: 85%;
          animation: fadeIn 0.3s ease;
        }
        .message.user { align-self: flex-end; flex-direction: row-reverse; }
        .message.assistant { align-self: flex-start; }
        .message-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          background: var(--glass-highlight);
          color: var(--text-dim);
        }
        .message.user .message-avatar { background: var(--primary-glow); color: var(--primary); }
        .message-content {
          padding: 12px 16px;
          border-radius: 16px;
          background: var(--glass-card);
          border: 1px solid var(--glass-border);
        }
        .message.user .message-content { background: var(--primary-glow); border-color: var(--primary); }
        .message-text { line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
        .message-sources { margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--glass-border); }
        .message-sources details { cursor: pointer; }
        .message-sources summary { font-size: 0.8rem; color: var(--text-dim); }
        .source-item { padding: 8px; margin: 4px 0; border-radius: 8px; background: rgba(255,255,255,0.03); font-size: 0.85rem; }
        .source-name { font-weight: 600; color: var(--primary); margin-bottom: 4px; }
        .source-text { color: var(--text-muted); font-size: 0.8rem; }
        .source-score { color: var(--text-dim); font-size: 0.75rem; margin-top: 4px; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </motion.div>
  )
}
