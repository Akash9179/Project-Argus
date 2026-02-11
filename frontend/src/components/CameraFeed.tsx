import { useState } from 'react'
import { SourceStatus, PERCEPTION_URL } from '@/types'

interface CameraFeedProps {
  sourceId: string
  name: string
  status?: SourceStatus
  large?: boolean
}

export function CameraFeed({ sourceId, name, status, large = false }: CameraFeedProps) {
  const [imgError, setImgError] = useState(false)
  const isOnline = status?.state === 'online' || status?.state === 'degraded'
  const streamUrl = `${PERCEPTION_URL}/stream/${sourceId}`

  return (
    <div
      className={`
        relative overflow-hidden bg-black
        border border-argus-border group
        ${large ? 'col-span-2 row-span-2' : ''}
        ${isOnline ? 'argus-border-glow' : ''}
      `}
    >
      {/* Video Feed */}
      {isOnline && !imgError ? (
        <img
          src={streamUrl}
          alt={name}
          className="w-full h-full object-cover"
          onError={() => setImgError(true)}
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-argus-primary">
          <div className="text-center">
            <div className="font-mono text-xxs text-argus-neutral tracking-widest mb-1">
              {imgError ? 'STREAM ERROR' : 'NO SIGNAL'}
            </div>
            <div className="font-mono text-xxs text-argus-neutral/50">
              {sourceId.slice(0, 8)}
            </div>
          </div>
        </div>
      )}

      {/* Top overlay: camera name + status */}
      <div className="absolute top-0 left-0 right-0 p-2 bg-gradient-to-b from-black/70 to-transparent">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FeedStatusDot state={status?.state ?? 'offline'} />
            <span className="font-mono text-xxs font-semibold tracking-wider text-white/90 uppercase">
              {name}
            </span>
          </div>
          {isOnline && (
            <span className="font-mono text-xxs tabular-nums text-argus-accent">
              {status?.fps_current.toFixed(0) ?? '—'} FPS
            </span>
          )}
        </div>
      </div>

      {/* Bottom overlay: metadata */}
      <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/70 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200">
        <div className="flex items-center justify-between">
          <span className="font-mono text-xxs text-white/50 tabular-nums">
            ID: {sourceId.slice(0, 8)}
          </span>
          {status && (
            <div className="flex items-center gap-3">
              <span className="font-mono text-xxs text-white/50 tabular-nums">
                {status.frames_total.toLocaleString()} frames
              </span>
              <span className="font-mono text-xxs text-white/50 tabular-nums">
                {status.latency_ms.toFixed(0)}ms
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Corner bracket decoration */}
      <CornerBrackets active={isOnline} />

      {/* Scanline effect on live feeds */}
      {isOnline && <div className="absolute inset-0 scanline pointer-events-none" />}
    </div>
  )
}

function FeedStatusDot({ state }: { state: string }) {
  const color = {
    online: '#30D158',
    degraded: '#FF9500',
    connecting: '#FF9500',
    offline: '#6B7280',
    error: '#FF3B30',
  }[state] ?? '#6B7280'

  return (
    <span
      className="inline-block w-1.5 h-1.5 rounded-full"
      style={{ backgroundColor: color }}
    />
  )
}

function CornerBrackets({ active }: { active: boolean }) {
  const color = active ? 'border-argus-accent/30' : 'border-argus-neutral/10'
  const size = 'w-3 h-3'

  return (
    <>
      {/* Top-left */}
      <span className={`absolute top-1 left-1 ${size} border-t border-l ${color}`} />
      {/* Top-right */}
      <span className={`absolute top-1 right-1 ${size} border-t border-r ${color}`} />
      {/* Bottom-left */}
      <span className={`absolute bottom-1 left-1 ${size} border-b border-l ${color}`} />
      {/* Bottom-right */}
      <span className={`absolute bottom-1 right-1 ${size} border-b border-r ${color}`} />
    </>
  )
}
