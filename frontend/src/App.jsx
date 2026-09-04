import { useState } from 'react'
import Heartbeat from './components/Heartbeat.jsx'
import TickLog from './components/TickLog.jsx'
import BacktestPanel from './components/BacktestPanel.jsx'
import { useLiveFeed } from './hooks/useLiveFeed.js'

const TABS = [
  { id: 'live', label: 'Live monitor' },
  { id: 'backtest', label: 'Backtest' },
]

export default function App() {
  const [tab, setTab] = useState('backtest')
  const { connected, ticks, halted } = useLiveFeed()

  return (
    <div className="flex h-screen flex-col bg-base text-ink">
      <header className="flex items-center justify-between border-b border-line px-5 py-3">
        <div className="flex items-center gap-3">
          <div className="h-2 w-2 rotate-45 bg-signal" />
          <h1 className="font-sans text-sm font-bold uppercase tracking-[0.15em]">
            TradeSentinel
          </h1>
        </div>
        <Heartbeat ticks={ticks} connected={connected} />
      </header>

      {halted && (
        <div className="border-b border-warn/40 bg-warn/10 px-5 py-2 font-mono text-xs text-warn">
          ⚠ {halted}
        </div>
      )}

      <nav className="flex border-b border-line px-5">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`border-b-2 px-4 py-2.5 font-mono text-xs uppercase tracking-wider transition-colors ${
              tab === t.id
                ? 'border-signal text-ink'
                : 'border-transparent text-muted hover:text-ink'
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="flex-1 overflow-hidden">
        {tab === 'live' && <TickLog ticks={ticks} />}
        {tab === 'backtest' && <BacktestPanel />}
      </main>
    </div>
  )
}
