import { useState, useEffect, useCallback } from 'react'
import { TopBar } from '@/components/TopBar'
import { CameraFeed } from '@/components/CameraFeed'
import { AddSourcePanel } from '@/components/AddSourcePanel'
import { IntelFeed } from '@/components/IntelFeed'
import { SystemStatus } from '@/components/SystemStatus'
import { useStatusWS } from '@/hooks/useStatusWS'

export default function App() {
  const { data: statusData, connected: wsConnected } = useStatusWS()
  const [tick, setTick] = useState(0)

  // Clock tick for TopBar time display
  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), 1000)
    return () => clearInterval(interval)
  }, [])

  // Get list of active source IDs from status
  const activeSources = statusData?.sources
    ? Object.entries(statusData.sources).map(([id, status]) => ({
        id,
        status,
        name: `SOURCE ${id.slice(-4).toUpperCase()}`,
      }))
    : []

  const handleSourceAdded = useCallback(() => {
    // Status will auto-update via WebSocket
  }, [])

  return (
    <div className="h-screen flex flex-col bg-argus-primary">
      {/* Top navigation bar */}
      <TopBar status={statusData} wsConnected={wsConnected} />

      {/* Main content area */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left: Camera grid + controls */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Status strip */}
          <div className="h-7 bg-argus-secondary/50 border-b border-argus-border flex items-center px-4 gap-4">
            <span className="argus-label">LAYER 1 — INGEST</span>
            <div className="w-px h-3 bg-argus-border" />
            <span className="font-mono text-xxs text-argus-neutral tabular-nums">
              {activeSources.length} ACTIVE SOURCE{activeSources.length !== 1 ? 'S' : ''}
            </span>
            {statusData && (
              <>
                <div className="w-px h-3 bg-argus-border" />
                <span className="font-mono text-xxs text-argus-accent tabular-nums">
                  {Object.values(statusData.sources).reduce((sum, s) => sum + s.frames_total, 0).toLocaleString()} FRAMES
                </span>
              </>
            )}
          </div>

          {/* Camera grid area */}
          <div className="flex-1 p-3 overflow-auto">
            {activeSources.length === 0 ? (
              <EmptyState />
            ) : (
              <div
                className={`
                  grid gap-2 h-full
                  ${activeSources.length === 1
                    ? 'grid-cols-1'
                    : activeSources.length <= 4
                      ? 'grid-cols-2'
                      : 'grid-cols-3'
                  }
                `}
              >
                {activeSources.map((source, i) => (
                  <CameraFeed
                    key={source.id}
                    sourceId={source.id}
                    name={source.name}
                    status={source.status}
                    large={activeSources.length === 3 && i === 0}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right sidebar */}
        <aside className="w-72 border-l border-argus-border flex flex-col gap-0 overflow-auto bg-argus-primary">
          {/* Add source panel */}
          <div className="p-3 border-b border-argus-border">
            <AddSourcePanel onSourceAdded={handleSourceAdded} />
          </div>

          {/* System status */}
          <div className="p-3 border-b border-argus-border">
            <SystemStatus status={statusData} />
          </div>

          {/* Intel feed */}
          <div className="flex-1 p-3">
            <IntelFeed />
          </div>
        </aside>
      </main>

      {/* Bottom status bar */}
      <footer className="h-6 bg-argus-secondary border-t border-argus-border flex items-center px-4 justify-between">
        <div className="flex items-center gap-3">
          <span className="font-mono text-xxs text-argus-neutral/50">
            ARGUS C2 v0.1.0
          </span>
          <div className="w-px h-3 bg-argus-border" />
          <span className="font-mono text-xxs text-argus-neutral/50">
            BACKEND :8000
          </span>
          <div className="w-px h-3 bg-argus-border" />
          <span className="font-mono text-xxs text-argus-neutral/50">
            PERCEPTION :8100
          </span>
        </div>
        <span className="font-mono text-xxs text-argus-neutral/30">
          LAYER 1: INGEST ● LAYER 2: PENDING
        </span>
      </footer>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="h-full flex items-center justify-center">
      <div className="text-center space-y-4 max-w-sm">
        {/* Decorative grid */}
        <div className="grid grid-cols-3 gap-1.5 w-32 mx-auto opacity-30">
          {Array.from({ length: 9 }).map((_, i) => (
            <div
              key={i}
              className="aspect-video bg-argus-tertiary border border-argus-border"
            />
          ))}
        </div>

        <div>
          <p className="font-mono text-xs text-argus-neutral-light tracking-wider">
            NO ACTIVE SOURCES
          </p>
          <p className="font-mono text-xxs text-argus-neutral mt-1.5 leading-relaxed">
            Add a camera source using the panel on the right.
            <br />
            Start with your webcam for a quick test.
          </p>
        </div>

        <div className="flex items-center justify-center gap-2 pt-2">
          <span className="w-8 h-px bg-argus-border" />
          <span className="font-mono text-xxs text-argus-neutral/40 tracking-[0.2em]">
            ARGUS C2
          </span>
          <span className="w-8 h-px bg-argus-border" />
        </div>
      </div>
    </div>
  )
}
