import { useState, useEffect, useRef } from 'react'
import { runCollaboration } from '../services/api'
import ProductCard from '../components/ProductCard'
import { motion, AnimatePresence } from 'framer-motion'
import type { Product } from '../types'

interface CollaborationResult {
  summary: string
  products: Product[]
}

export default function Dashboard() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<CollaborationResult | null>(null)
  const [logs, setLogs] = useState<{ msg: string; type: string }[]>([])
  const logEndRef = useRef<HTMLDivElement>(null)

  const addLog = (msg: string, type: string = 'info') => {
    setLogs(prev => [...prev, { msg, type }])
  }

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const handleCollaboration = async () => {
    if (!query.trim()) return
    setLoading(true)
    setResult(null)
    setLogs([])
    
    addLog('> Initializing Council connection...', 'primary')
    setTimeout(() => addLog('> Analyzing mission objectives: "' + query + '"'), 400)
    setTimeout(() => addLog('> Dispatching Researcher-01 to global catalog...', 'info'), 1200)
    setTimeout(() => addLog('> Researcher found matches. Transferring data to Auditor...', 'success'), 2200)
    setTimeout(() => addLog('> Auditor verifying market prices across 5 retailers...', 'info'), 3200)
    setTimeout(() => addLog('> Auditor identified 2 critical discounts.', 'success'), 4500)
    setTimeout(() => addLog('> Stylist finalizing aesthetic and rating priority...', 'info'), 5500)
    setTimeout(() => addLog('> Synthesis complete. Presenting verdict.', 'primary'), 6500)

    try {
      const data = await runCollaboration(query)
      setTimeout(() => {
        setResult(data)
        setLoading(false)
      }, 7000)
    } catch (err) {
      addLog(`! System Error: ${err instanceof Error ? err.message : 'Failed to reach Council.'}`, 'danger')
      setLoading(false)
    }
  }

  return (
    <div className="reveal">
      <div className="page-header" style={{ marginBottom: '3rem' }}>
        <div className="page-header-left">
          <motion.h1 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="page-title"
          >
            Collaboration Council
          </motion.h1>
          <p className="page-subtitle">Harness the collective intelligence of your autonomous agents</p>
        </div>
      </div>

      <motion.div 
        layout
        className="glass-panel" 
        style={{ padding: '2.5rem', borderRadius: '24px', marginBottom: '3rem', position: 'relative', overflow: 'hidden' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', marginBottom: '2rem' }}>
          <div className="logo-icon-glow" style={{ width: '50px', height: '40px', flexShrink: 0 }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.25rem', letterSpacing: '-0.02em' }}>Initiate Council Deliberation</h3>
            <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-muted)' }}>Agents will collaborate to find, audit, and curate the best matches for your operational needs.</p>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <input 
            className="input" 
            placeholder="e.g. 'I need high-performance wireless earbuds under $200'" 
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleCollaboration()}
            style={{ flex: 1, minWidth: '280px', height: '56px', fontSize: '1.05rem', background: 'rgba(255,255,255,0.02)', borderRadius: '16px' }}
            aria-label="Enter your shopping query"
          />
          <motion.button 
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="btn-cyber" 
            onClick={handleCollaboration} 
            disabled={loading}
            style={{ height: '56px', padding: '0 2.5rem', borderRadius: '16px', flexShrink: 0 }}
          >
            {loading ? 'Processing...' : 'Ask Council'}
          </motion.button>
        </div>

        {loading && (
          <div className="tactical-log">
            {logs.map((log, i) => (
              <div key={i} className={`log-entry ${log.type}`}>
                <span style={{ opacity: 0.4 }}>[{new Date().toLocaleTimeString().split(' ')[0]}]</span>
                <span>{log.msg}</span>
              </div>
            ))}
            <div ref={logEndRef} />
          </div>
        )}

        {loading && (
          <motion.div 
            initial={{ width: 0 }}
            animate={{ width: '100%' }}
            transition={{ duration: 7, ease: 'linear' }}
            style={{ position: 'absolute', bottom: 0, left: 0, height: '3px', background: 'linear-gradient(90deg, var(--primary), var(--secondary))' }}
          />
        )}
      </motion.div>

      <AnimatePresence>
        {result && (
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: 'spring', damping: 20 }}
          >
            <div className="glass-panel" style={{ marginBottom: '2.5rem', padding: '2rem', borderRadius: '20px', borderLeft: '4px solid var(--primary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.25rem' }}>
                <span style={{ color: 'var(--primary)', fontWeight: '800', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.15em' }}>Council Verdict</span>
                <div style={{ flex: 1, height: '1px', background: 'var(--glass-border)' }} />
              </div>
              <motion.p 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                style={{ fontSize: '1.2rem', color: 'var(--text)', lineHeight: '1.6', fontWeight: 500 }}
              >
                {result.summary}
              </motion.p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.03em' }}>Curated Selections</h2>
              <span className="status-pill" style={{ background: 'var(--primary-glow)', color: 'var(--primary)' }}>
                {result.products.length} High-Fidelity Matches
              </span>
            </div>

            <motion.div 
              layout
              className="grid"
              style={{ gap: '1.5rem' }}
            >
              {result.products.map((p, i) => (
                <motion.div
                  key={p.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                >
                  <ProductCard product={p} />
                </motion.div>
              ))}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {!result && !loading && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="empty-state" 
          style={{ padding: '8rem 2rem' }}
        >
          <div className="logo-icon-glow" style={{ width: '80px', height: '80px', margin: '0 auto 2rem', opacity: 0.5 }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          </div>
          <h3 style={{ color: 'var(--text-muted)', fontSize: '1.25rem' }}>Council is Operational</h3>
          <p style={{ maxWidth: '420px', margin: '1rem auto 0', lineHeight: '1.6', color: 'var(--text-dim)' }}>
            Your collective workforce is idling in standby mode. Provide a mission objective to initiate collaborative processing.
          </p>
        </motion.div>
      )}
    </div>
  )
}
