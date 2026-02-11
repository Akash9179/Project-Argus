import { StatusMessage, SourceStatus } from '@/types'

interface SystemStatusProps {
  status: StatusMessage | null
}

export function SystemStatus({ status }: SystemStatusProps) {
  const sources = status?.sources ? Object.values(status.sources) : []

  return (
    <div className="argus-card">
      <div className="px-3 py-2.5 border-b border-argus-border flex items-center justify-between">
        <span className="argus-label">SYSTEM STATUS</span>
        <div className="flex items-center gap-2">
          <span className="font-mono text-xxs tabular-nums text-alert-success">
            {status?.online ?? 0}
          </span>
          <span className="font-mono text-xxs text-argus-neutral">/</span>
          <span className="font-mono text-xxs tabular-nums text-argus-neutral-light">
            {status?.total ?? 0}
          </span>
        </div>
      </div>

      <div className="p-3 space-y-2">
        {sources.length === 0 ? (
          <p className="font-mono text-xxs text-argus-neutral/50 text-center py-4">
            No active sources
          </p>
        ) : (
          sources.map((s) => <SourceRow key={s.source_id} status={s} />)
        )}
      </div>
    </div>
  )
}

function SourceRow({ status }: { status: SourceStatus }) {
  const stateColor = {
    online: 'text-alert-success',
    degraded: 'text-alert-warning',
    connecting: 'text-alert-warning',
    offline: 'text-argus-neutral',
    error: 'text-alert-critical',
  }[status.state] ?? 'text-argus-neutral'

  const stateBg = {
    online: 'bg-alert-success',
    degraded: 'bg-alert-warning',
    connecting: 'bg-alert-warning',
    offline: 'bg-argus-neutral',
    error: 'bg-alert-critical',
  }[status.state] ?? 'bg-argus-neutral'

  return (
    <div className="flex items-center gap-3 px-2 py-1.5 hover:bg-argus-primary/50 transition-colors group">
      <span className={`w-1.5 h-1.5 rounded-full ${stateBg} shrink-0`} />

      <div className="flex-1 min-w-0">
        <div className="font-mono text-xxs text-argus-light truncate">
          {status.source_id.slice(0, 8)}
        </div>
      </div>

      <span className={`font-mono text-xxs uppercase tracking-wider ${stateColor}`}>
        {status.state}
      </span>

      <span className="font-mono text-xxs tabular-nums text-argus-neutral-light w-12 text-right">
        {status.fps_current.toFixed(0)} fps
      </span>

      <span className="font-mono text-xxs tabular-nums text-argus-neutral w-14 text-right">
        {formatUptime(status.uptime_s)}
      </span>
    </div>
  )
}

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(0)}s`
  if (seconds < 3600) return `${(seconds / 60).toFixed(0)}m`
  return `${(seconds / 3600).toFixed(1)}h`
}
