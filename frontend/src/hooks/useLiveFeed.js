import { useEffect, useRef, useState } from 'react'

const MAX_TICKS = 200

export function useLiveFeed() {
  const [connected, setConnected] = useState(false)
  const [ticks, setTicks] = useState([])
  const [lastTrade, setLastTrade] = useState(null)
  const [halted, setHalted] = useState(null)
  const wsRef = useRef(null)

  useEffect(() => {
    let reconnectTimer
    let closedByCleanup = false

    function connect() {
      const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const ws = new WebSocket(`${proto}://${window.location.host}/api/v1/ws/live`)
      wsRef.current = ws

      ws.onopen = () => setConnected(true)
      ws.onclose = () => {
        setConnected(false)
        if (!closedByCleanup) {
          reconnectTimer = setTimeout(connect, 2000)
        }
      }
      ws.onerror = () => ws.close()
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'tick') {
            setTicks((prev) => [...prev.slice(-(MAX_TICKS - 1)), data])
            if (data.trade) setLastTrade({ ...data.trade, symbol: data.symbol, at: Date.now() })
          } else if (data.type === 'halt') {
            setHalted(data.reason)
          }
        } catch {
          // ignore malformed frames
        }
      }
    }

    connect()
    return () => {
      closedByCleanup = true
      clearTimeout(reconnectTimer)
      wsRef.current?.close()
    }
  }, [])

  return { connected, ticks, lastTrade, halted }
}
