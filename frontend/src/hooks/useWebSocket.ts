import { useEffect, useRef } from 'react'

export interface WsEvent {
  type: 'review.completed' | 'scan.progress' | 'scan.completed'
  repo_id: number
  data: Record<string, unknown>
}

type EventHandler = (event: WsEvent) => void

const WS_URL = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`

/**
 * Opens a persistent WebSocket connection to /ws and calls `onEvent` for each
 * received message. Automatically reconnects on close/error with exponential
 * back-off (up to 30 s). The connection is cleaned up on component unmount.
 */
export function useWebSocket(onEvent: EventHandler) {
  const onEventRef = useRef<EventHandler>(onEvent)
  onEventRef.current = onEvent

  useEffect(() => {
    let ws: WebSocket | null = null
    let retryDelay = 1000
    let unmounted = false
    let retryTimer: ReturnType<typeof setTimeout> | null = null

    function connect() {
      if (unmounted) return
      ws = new WebSocket(WS_URL)

      ws.onopen = () => {
        retryDelay = 1000 // reset back-off on successful connect
      }

      ws.onmessage = (event) => {
        try {
          const parsed: WsEvent = JSON.parse(event.data as string)
          onEventRef.current(parsed)
        } catch {
          // ignore malformed messages
        }
      }

      ws.onclose = () => {
        if (!unmounted) {
          const delay = retryDelay
          retryDelay = Math.min(retryDelay * 2, 30_000)
          retryTimer = setTimeout(connect, delay)
        }
      }

      ws.onerror = () => {
        ws?.close()
      }
    }

    connect()

    return () => {
      unmounted = true
      if (retryTimer) clearTimeout(retryTimer)
      ws?.close()
    }
  }, [])
}
