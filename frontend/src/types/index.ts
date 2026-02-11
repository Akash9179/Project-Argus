// ─── Source Types ────────────────────────────────────

export type SourceType = 'rtsp' | 'onvif' | 'usb' | 'file' | 'mjpeg' | 'screen'
export type SourceDomain = 'air' | 'land' | 'water'
export type SourceState = 'connecting' | 'online' | 'degraded' | 'offline' | 'error'

export interface SourceLocation {
  lat?: number
  lon?: number
  facility_x?: number
  facility_y?: number
  fov_angle?: number
  fov_width?: number
}

export interface Source {
  id: string
  name: string
  type: SourceType
  uri: string
  enabled: boolean
  target_fps: number
  native_fps?: number
  resolution_w?: number
  resolution_h?: number
  domain: SourceDomain
  zone_id?: string
  location?: SourceLocation
  vendor?: string
  model?: string
  created_at: string
  updated_at: string
}

export interface SourceStatus {
  source_id: string
  state: SourceState
  fps_current: number
  fps_target: number
  frames_total: number
  frames_dropped: number
  last_frame_at?: string
  uptime_s: number
  error?: string
  reconnect_count: number
  latency_ms: number
}

// ─── WebSocket Messages ─────────────────────────────

export interface StatusMessage {
  type: 'source_status'
  total: number
  online: number
  sources: Record<string, SourceStatus>
}

// ─── Config ─────────────────────────────────────────

export const PERCEPTION_URL = 'http://localhost:8100'
export const BACKEND_URL = 'http://localhost:8000'
export const WS_STATUS_URL = 'ws://localhost:8100/ws/status'
