import { useState } from 'react'
import { PERCEPTION_URL, BACKEND_URL } from '@/types'

interface AddSourcePanelProps {
  onSourceAdded: () => void
}

const PRESETS = [
  { label: 'Webcam', type: 'usb', uri: '0', icon: '📷' },
  { label: 'Video File', type: 'file', uri: '', icon: '🎬' },
  { label: 'RTSP Stream', type: 'rtsp', uri: 'rtsp://', icon: '📡' },
  { label: 'MJPEG/HTTP', type: 'mjpeg', uri: 'http://', icon: '🌐' },
]

export function AddSourcePanel({ onSourceAdded }: AddSourcePanelProps) {
  const [name, setName] = useState('')
  const [sourceType, setSourceType] = useState('usb')
  const [uri, setUri] = useState('0')
  const [fps, setFps] = useState(10)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || !uri.trim()) return

    setLoading(true)
    setError(null)
    setSuccess(false)

    const sourceId = crypto.randomUUID()

    try {
      // 1. Save to backend DB
      await fetch(`${BACKEND_URL}/api/v1/sources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          type: sourceType,
          uri: uri.trim(),
          domain: 'land',
          target_fps: fps,
        }),
      })

      // 2. Start capture in perception service
      const res = await fetch(`${PERCEPTION_URL}/sources/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_id: sourceId,
          name: name.trim(),
          source_type: sourceType,
          uri: uri.trim(),
          target_fps: fps,
        }),
      })

      if (!res.ok) {
        const detail = await res.json()
        throw new Error(detail.detail || 'Failed to start source')
      }

      setSuccess(true)
      setName('')
      onSourceAdded()

      setTimeout(() => setSuccess(false), 2000)
    } catch (err: any) {
      setError(err.message || 'Connection failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="argus-card p-4">
      <h3 className="argus-label mb-3">ADD SOURCE</h3>

      {/* Quick presets */}
      <div className="flex gap-2 mb-3">
        {PRESETS.map((p) => (
          <button
            key={p.type}
            onClick={() => {
              setSourceType(p.type)
              setUri(p.uri)
              if (!name) setName(p.label)
            }}
            className={`
              flex items-center gap-1.5 px-2.5 py-1.5
              font-mono text-xxs tracking-wider
              border transition-colors duration-150
              ${sourceType === p.type
                ? 'border-argus-accent/40 bg-argus-accent/5 text-argus-accent'
                : 'border-argus-border text-argus-neutral hover:text-argus-neutral-light hover:border-argus-border-light'
              }
            `}
          >
            <span>{p.icon}</span>
            <span>{p.label.toUpperCase()}</span>
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-2.5">
        <div className="grid grid-cols-2 gap-2.5">
          <div>
            <label className="argus-label text-xxs block mb-1">NAME</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Entry Gate"
              className="w-full bg-argus-primary border border-argus-border px-2.5 py-1.5 font-mono text-xs text-argus-light placeholder:text-argus-neutral/40 focus:border-argus-accent/40 focus:outline-none transition-colors"
            />
          </div>
          <div>
            <label className="argus-label text-xxs block mb-1">FPS</label>
            <input
              type="number"
              value={fps}
              onChange={(e) => setFps(parseInt(e.target.value) || 10)}
              min={1}
              max={30}
              className="w-full bg-argus-primary border border-argus-border px-2.5 py-1.5 font-mono text-xs text-argus-light focus:border-argus-accent/40 focus:outline-none transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="argus-label text-xxs block mb-1">URI</label>
          <input
            type="text"
            value={uri}
            onChange={(e) => setUri(e.target.value)}
            placeholder="rtsp://192.168.1.100:554/stream1"
            className="w-full bg-argus-primary border border-argus-border px-2.5 py-1.5 font-mono text-xs text-argus-light placeholder:text-argus-neutral/40 focus:border-argus-accent/40 focus:outline-none transition-colors"
          />
        </div>

        <button
          type="submit"
          disabled={loading || !name.trim() || !uri.trim()}
          className={`
            w-full py-2 font-mono text-xxs font-semibold tracking-[0.15em] uppercase
            border transition-all duration-200
            ${loading
              ? 'border-argus-border text-argus-neutral cursor-wait'
              : success
                ? 'border-alert-success/40 bg-alert-success/5 text-alert-success'
                : 'border-argus-accent/30 bg-argus-accent/5 text-argus-accent hover:bg-argus-accent/10 hover:border-argus-accent/50'
            }
            disabled:opacity-30 disabled:cursor-not-allowed
          `}
        >
          {loading ? 'CONNECTING...' : success ? '✓ SOURCE ADDED' : '+ ADD SOURCE'}
        </button>

        {error && (
          <p className="font-mono text-xxs text-alert-critical">{error}</p>
        )}
      </form>
    </div>
  )
}
