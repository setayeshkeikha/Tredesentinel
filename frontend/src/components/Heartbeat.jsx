import { useMemo } from 'react'

/**
 * The signature element: a continuous, ambient sparkline of portfolio value
 * ticking in real time in the header — like a heartbeat monitor. It never
 * announces itself with a label larger than a caption; it just quietly
 * proves the bot is alive.
 */
export default function Heartbeat({ ticks, connected }) {
  const path = useMemo(() => {
    const values = ticks.map((t) => t.portfolio_value).filter((v) => typeof v === 'number')
    if (values.length < 2) return ''
    const min = Math.min(...values)
    const max = Math.max(...values)
    const range = max - min || 1
    const w = 240
    const h = 40
    const step = w / (values.length - 1)
    return values
      .map((v, i) => {
        const x = i * step
        const y = h - ((v - min) / range) * h
        return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
      })
      .join(' ')
  }, [ticks])

  const latest = ticks[ticks.length - 1]

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-1.5">
        <span
          className={`h-1.5 w-1.5 rounded-full ${connected ? 'bg-signal pulse-dot' : 'bg-danger'}`}
        />
        <span className="font-mono text-2xs uppercase tracking-wider text-muted">
          {connected ? 'live' : 'reconnecting'}
        </span>
      </div>
      <svg width="240" height="40" className="overflow-visible">
        {path && (
          <path
            d={path}
            fill="none"
            stroke="#00D9A3"
            strokeWidth="1.25"
            strokeLinejoin="round"
            strokeLinecap="round"
            opacity="0.9"
          />
        )}
      </svg>
      {latest && (
        <span className="font-mono text-sm text-ink tabular-nums">
          ${latest.portfolio_value?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
        </span>
      )}
    </div>
  )
}
