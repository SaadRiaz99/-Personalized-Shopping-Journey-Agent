import type { Document } from '../types'

interface Props {
  document: Document
  onDelete?: (id: string) => void
  selected?: boolean
  onToggle?: (id: string) => void
}

export default function DocumentCard({ document: doc, onDelete, selected, onToggle }: Props) {
  const sizeStr = doc.file_size > 1024 * 1024
    ? `${(doc.file_size / (1024 * 1024)).toFixed(1)} MB`
    : `${(doc.file_size / 1024).toFixed(1)} KB`

  const statusColors: Record<string, string> = {
    uploaded: 'var(--text-dim)',
    processing: 'var(--warning)',
    processed: 'var(--success)',
    error: 'var(--danger)',
  }

  return (
    <div className={`document-card ${selected ? 'selected' : ''}`} onClick={() => onToggle?.(doc.id)}>
      <div className="doc-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="24" height="24">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
      </div>
      <div className="doc-info">
        <div className="doc-name">{doc.filename}</div>
        <div className="doc-meta">
          <span style={{ color: statusColors[doc.status] || 'var(--text-dim)' }}>{doc.status}</span>
          <span>{sizeStr}</span>
          {doc.chunk_count > 0 && <span>{doc.chunk_count} chunks</span>}
        </div>
      </div>
      {onDelete && (
        <button className="doc-delete" onClick={(e) => { e.stopPropagation(); onDelete(doc.id) }}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
        </button>
      )}

      <style>{`
        .document-card {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          border-radius: 12px;
          background: var(--glass-card);
          border: 1px solid var(--glass-border);
          cursor: pointer;
          transition: var(--transition-smooth);
        }
        .document-card:hover { background: var(--glass-highlight); }
        .document-card.selected { border-color: var(--primary); background: var(--primary-glow); }
        .doc-icon { color: var(--primary); flex-shrink: 0; }
        .doc-info { flex: 1; min-width: 0; }
        .doc-name { font-weight: 600; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .doc-meta { display: flex; gap: 12px; font-size: 0.8rem; color: var(--text-dim); margin-top: 4px; }
        .doc-delete {
          background: none;
          border: none;
          color: var(--text-dim);
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
          transition: var(--transition-smooth);
        }
        .doc-delete:hover { color: var(--danger); background: rgba(255,0,0,0.1); }
      `}</style>
    </div>
  )
}
