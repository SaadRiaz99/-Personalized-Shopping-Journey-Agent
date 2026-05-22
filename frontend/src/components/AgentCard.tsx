import type { Agent } from '../types'

interface Props {
  agent: Agent
  onRun: (id: string) => void
  onDelete: (id: string) => void
}

const statusColors: Record<string, string> = {
  idle: '#6b7280',
  running: '#3b82f6',
  completed: '#2bd47c',
  error: '#ef5566',
}

export default function AgentCard({ agent, onRun, onDelete }: Props) {
  return (
    <div className="card">
      <div className="card-header">
        <h3>{agent.name}</h3>
        <span
          className="status"
          style={{ background: `${statusColors[agent.status]}20`, color: statusColors[agent.status] }}
        >
          <span className="status-dot" style={{ background: statusColors[agent.status] }} />
          {agent.status}
        </span>
      </div>
      {agent.task && <p className="task-text">{agent.task}</p>}
      <div className="card-actions">
        <button
          className="btn btn-primary"
          onClick={() => onRun(agent.id)}
          disabled={agent.status === 'running'}
        >
          ▶ Run
        </button>
        <button className="btn btn-danger" onClick={() => onDelete(agent.id)}>
          ✕ Delete
        </button>
      </div>
    </div>
  )
}
