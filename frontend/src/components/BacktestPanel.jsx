import { useState } from 'react'
import EquityChart from './EquityChart.jsx'
import { api } from '../lib/api.js'

const STRATEGY_FIELDS = {
  rsi: [
    { key: 'period', label: 'Period', default: 14 },
    { key: 'oversold', label: 'Oversold', default: 30 },
    { key: 'overbought', label: 'Overbought', default: 70 },
  ],
  macd: [
    { key: 'fast', label: 'Fast EMA', default: 12 },
    { key: 'slow', label: 'Slow EMA', default: 26 },
    { key: 'signal_period', label: 'Signal', default: 9 },
  ],
  grid: [
    { key: 'lower_bound', label: 'Lower bound', default: 90000 },
    { key: 'upper_bound', label: 'Upper bound', default: 110000 },
    { key: 'grid_levels', label: 'Grid levels', default: 10 },
  ],
}

export default function BacktestPanel() {
  const [symbol, setSymbol] = useState('BTC/USDT')
  const [timeframe, setTimeframe] = useState('1h')
  const [strategyName, setStrategyName] = useState('rsi')
  const [params, setParams] = useState(
    Object.fromEntries(STRATEGY_FIELDS.rsi.map((f) => [f.key, f.default])),
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [report, setReport] = useState(null)

  function selectStrategy(name) {
    setStrategyName(name)
    setParams(Object.fromEntries(STRATEGY_FIELDS[name].map((f) => [f.key, f.default])))
  }

  function updateParam(key, value) {
    setParams((prev) => ({ ...prev, [key]: Number(value) }))
  }

  async function handleRun() {
    setLoading(true)
    setError(null)
    try {
      const result = await api.runBacktest({
        symbol,
        timeframe,
        strategy_name: strategyName,
        strategy_params: params,
        candle_limit: 500,
        starting_equity: 10000,
      })
      setReport(result)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid h-full grid-cols-[280px_1fr]">
      <div className="border-r border-line p-4">
        <h2 className="mb-4 font-sans text-xs font-semibold uppercase tracking-wider text-muted">
          Backtest configuration
        </h2>

        <label className="mb-1 block font-mono text-2xs uppercase text-muted">Symbol</label>
        <input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          className="mb-3 w-full border border-line bg-panel2 px-2 py-1.5 font-mono text-sm text-ink outline-none focus:border-signal"
        />

        <label className="mb-1 block font-mono text-2xs uppercase text-muted">Timeframe</label>
        <select
          value={timeframe}
          onChange={(e) => setTimeframe(e.target.value)}
          className="mb-3 w-full border border-line bg-panel2 px-2 py-1.5 font-mono text-sm text-ink outline-none focus:border-signal"
        >
          {['15m', '1h', '4h', '1d'].map((tf) => (
            <option key={tf} value={tf}>{tf}</option>
          ))}
        </select>

        <label className="mb-1 block font-mono text-2xs uppercase text-muted">Strategy</label>
        <div className="mb-3 flex gap-1">
          {Object.keys(STRATEGY_FIELDS).map((name) => (
            <button
              key={name}
              onClick={() => selectStrategy(name)}
              className={`flex-1 border px-2 py-1.5 font-mono text-2xs uppercase transition-colors ${
                strategyName === name
                  ? 'border-signal bg-signal/10 text-signal'
                  : 'border-line text-muted hover:border-muted'
              }`}
            >
              {name}
            </button>
          ))}
        </div>

        {STRATEGY_FIELDS[strategyName].map((f) => (
          <div key={f.key} className="mb-3">
            <label className="mb-1 block font-mono text-2xs uppercase text-muted">{f.label}</label>
            <input
              type="number"
              value={params[f.key]}
              onChange={(e) => updateParam(f.key, e.target.value)}
              className="w-full border border-line bg-panel2 px-2 py-1.5 font-mono text-sm text-ink outline-none focus:border-signal"
            />
          </div>
        ))}

        <button
          onClick={handleRun}
          disabled={loading}
          className="mt-2 w-full border border-signal bg-signal/10 py-2 font-mono text-xs font-semibold uppercase tracking-wider text-signal transition-colors hover:bg-signal/20 disabled:opacity-40"
        >
          {loading ? 'Running…' : 'Run backtest'}
        </button>

        {error && (
          <p className="mt-3 border border-danger/40 bg-danger/10 px-2 py-1.5 font-mono text-2xs text-danger">
            {error}
          </p>
        )}
      </div>

      <div className="flex flex-col">
        <div className="h-64 border-b border-line p-2">
          {report ? (
            <EquityChart equityCurve={report.equity_curve} />
          ) : (
            <div className="flex h-full items-center justify-center font-mono text-xs text-muted">
              Configure a strategy and run a backtest to see the equity curve
            </div>
          )}
        </div>

        {report && (
          <div className="grid grid-cols-4 gap-px bg-line">
            <Metric label="Ending equity" value={`$${report.ending_equity.toLocaleString()}`} />
            <Metric label="Total trades" value={report.total_trades} />
            <Metric label="Win rate" value={`${(report.win_rate * 100).toFixed(1)}%`} />
            <Metric
              label="Max drawdown"
              value={`${(report.max_drawdown_pct * 100).toFixed(1)}%`}
              warn={report.max_drawdown_pct > 0.1}
            />
          </div>
        )}

        {report && (
          <div className="flex-1 overflow-y-auto">
            <table className="w-full font-mono text-xs">
              <thead className="sticky top-0 bg-panel">
                <tr className="border-b border-line text-left text-muted">
                  <th className="px-4 py-2 font-medium">Time</th>
                  <th className="px-2 py-2 font-medium">Side</th>
                  <th className="px-2 py-2 font-medium">Price</th>
                  <th className="px-2 py-2 font-medium">Amount</th>
                  <th className="px-2 py-2 font-medium">PnL</th>
                  <th className="px-4 py-2 font-medium">Reason</th>
                </tr>
              </thead>
              <tbody>
                {report.trades.map((t, i) => (
                  <tr key={i} className="border-b border-line/50 hover:bg-panel2">
                    <td className="px-4 py-1.5 text-muted">{new Date(t.timestamp).toLocaleString()}</td>
                    <td className={`px-2 py-1.5 font-semibold uppercase ${t.side === 'buy' ? 'text-signal' : 'text-warn'}`}>
                      {t.side}
                    </td>
                    <td className="px-2 py-1.5 tabular-nums text-ink">{t.price.toFixed(2)}</td>
                    <td className="px-2 py-1.5 tabular-nums text-ink">{t.amount.toFixed(6)}</td>
                    <td className={`px-2 py-1.5 tabular-nums ${t.pnl > 0 ? 'text-signal' : t.pnl < 0 ? 'text-danger' : 'text-muted'}`}>
                      {t.pnl != null ? t.pnl.toFixed(2) : '—'}
                    </td>
                    <td className="px-4 py-1.5 text-muted">{t.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function Metric({ label, value, warn }) {
  return (
    <div className="bg-panel px-4 py-3">
      <p className="mb-1 font-mono text-2xs uppercase tracking-wider text-muted">{label}</p>
      <p className={`font-mono text-lg font-semibold ${warn ? 'text-warn' : 'text-ink'}`}>{value}</p>
    </div>
  )
}
