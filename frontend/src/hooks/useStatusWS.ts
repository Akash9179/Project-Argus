import { useState, useEffect, useRef, useCallback } from 'react'
import { StatusMessage, WS_STATUS_URL } from '@/types'

interface UseStatusWSReturn {
  data: StatusMessage | null
  connected: boolean
  error: string | null
}

export function useStatusWS(): UseStatusWSReturn {
  const [data, setData] = useState<StatusMessage | null>(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(WS_STATUS_URL)

      ws.onopen = () => {
        setConnected(true)
        setError(null)
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data) as StatusMessage
          setData(msg)
        } catch {
          // ignore parse errors
        }
      }

      ws.onclose = () => {
        setConnected(false)
        wsRef.current = null
        // Reconnect after 3 seconds
        reconnectTimer.current = setTimeout(connect, 3000)
      }

      ws.onerror = () => {
        setError('WebSocket connection failed')
        ws.close()
      }

      wsRef.current = ws
    } catch {
      setError('Failed to create WebSocket')
      reconnectTimer.current = setTimeout(connect, 3000)
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      if (wsRef.current) wsRef.current.close()
    }
  }, [connect])

  return { data, connected, error }
}
