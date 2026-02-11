import { StatusMessage } from '@/types'

interface TopBarProps {
  status: StatusMessage | null
  wsConnected: boolean
}

function formatUptime(): string {
  const now = new Date()
  return now.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function TopBar({ status, wsConnected }: TopBarProps) {
  const online = status?.online ?? 0
  const total = status?.total ?? 0

  return (
    <header className="h-11 bg-argus-secondary border-b border-argus-border flex items-center justify-between px-4 shrink-0">
      {/* Left: Brand */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm font-bold tracking-[0.25em] text-white">
            ARGUS
          </span>
          <span className="font-mono text-xxs tracking-[0.15em] text-argus-neutral">
            C2
          </span>
        </div>

        <div className="w-px h-5 bg-argus-border" />

        {/* Nav tabs */}
        <nav className="flex items-center gap-1">
          <TabButton active>OPERATIONS</TabButton>
          <TabButton>ALERTS</TabButton>
          <TabButton>INVESTIGATE</TabButton>
          <TabButton>ANALYTICS</TabButton>
          <TabButton>ASSETS</TabButton>
        </nav>
      </div>

      {/* Right: Status indicators */}
      <div className="flex items-center gap-4">
        {/* Source count */}
        <div className="flex items-center gap-2">
          <StatusDot state={online > 0 ? 'online' : 'offline'} />
          <span className="font-mono text-xxs text-argus-neutral-light">
            {online}/{total} SOURCES
          </span>
        </div>

        <div className="w-px h-4 bg-argus-border" />

        {/* WebSocket status */}
        <div className="flex items-center gap-2">
          <StatusDot state={wsConnected ? 'online' : 'error'} />
          <span className="font-mono text-xxs text-argus-neutral-light">
            {wsConnected ? 'LIVE' : 'DISCONNECTED'}
          </span>
        </div>

        <div className="w-px h-4 bg-argus-border" />

        {/* Clock */}
        <Clock />
      </div>
    </header>
  )
}

function TabButton({ children, active = false }: { children: React.ReactNode; active?: boolean }) {
  return (
    <button
      className={`
        font-mono text-xxs tracking-[0.1em] px-3 py-1.5
        transition-colors duration-150
        ${active
          ? 'text-argus-accent bg-argus-accent/5 border-b border-argus-accent'
          : 'text-argus-neutral hover:text-argus-neutral-light'
        }
      `}
    >
      {children}
    </button>
  )
}

function StatusDot({ state }: { state: 'online' | 'offline' | 'error' | 'degraded' }) {
  const colors = {
    online: 'bg-alert-success',
    degraded: 'bg-alert-warning',
    offline: 'bg-argus-neutral',
    error: 'bg-alert-critical',
  }

  return (
    <span className="relative flex h-2 w-2">
      {state === 'online' && (
        <span className={`absolute inline-flex h-full w-full rounded-full ${colors[state]} opacity-40 status-pulse`} />
      )}
      <span className={`relative inline-flex rounded-full h-2 w-2 ${colors[state]}`} />
    </span>
  )
}

function Clock() {
  // Simple clock that updates via CSS trick (re-renders handled by parent)
  return (
    <span className="font-mono text-xxs tabular-nums text-argus-neutral-light">
      {formatUptime()}
    </span>
  )
}
