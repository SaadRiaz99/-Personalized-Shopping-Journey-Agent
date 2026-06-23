import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import DocumentCard from '../components/DocumentCard'
import { getDocuments, uploadDocument, deleteDocument } from '../services/api'
import type { Document } from '../types'

export default function Documents() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  const fetchDocs = useCallback(async () => {
    try {
      const res = await getDocuments()
      setDocuments(res.documents)
    } catch {
      setError('Failed to load documents')
    }
    setLoading(false)
  }, [])

  useEffect(() => { fetchDocs() }, [fetchDocs])

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError('')
    try {
      await uploadDocument(file)
      await fetchDocs()
    } catch {
      setError('Upload failed. Check file type and size.')
    }
    setUploading(false)
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteDocument(id)
      setDocuments(prev => prev.filter(d => d.id !== id))
    } catch {
      setError('Delete failed')
    }
  }

  const acceptedFormats = '.pdf,.docx,.txt'

  return (
    <div className="documents-page">
      <div className="page-header">
        <h2>Documents</h2>
        <label className="btn btn-primary upload-btn">
          {uploading ? 'Uploading...' : '+ Upload'}
          <input type="file" accept={acceptedFormats} onChange={handleUpload} hidden disabled={uploading} />
        </label>
      </div>

      {error && <div className="error-msg">{error}</div>}

      <div className="upload-info">
        <p className="text-dim" style={{ fontSize: '0.85rem' }}>Supported: PDF, DOCX, TXT (max 50MB)</p>
      </div>

      {loading ? (
        <div className="loading-state">Loading documents...</div>
      ) : documents.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </div>
          <h3>No documents yet</h3>
          <p className="text-dim">Upload PDF, DOCX, or TXT files to get started</p>
        </div>
      ) : (
        <motion.div className="documents-grid" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {documents.map(doc => (
            <DocumentCard key={doc.id} document={doc} onDelete={handleDelete} />
          ))}
        </motion.div>
      )}

      <style>{`
        .documents-page { max-width: 800px; margin: 0 auto; }
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
        .page-header h2 { margin: 0; }
        .upload-btn { cursor: pointer; padding: 10px 20px; }
        .upload-info { margin-bottom: 16px; }
        .documents-grid { display: flex; flex-direction: column; gap: 8px; }
        .error-msg { color: var(--danger); font-size: 0.85rem; padding: 8px 12px; border-radius: 8px; background: rgba(255,0,0,0.1); margin-bottom: 12px; }
        .loading-state, .empty-state { text-align: center; padding: 60px 20px; color: var(--text-dim); }
        .empty-icon { color: var(--primary); opacity: 0.3; margin-bottom: 16px; }
      `}</style>
    </div>
  )
}
