const SIGNAL_STYLES = {
  buy: 'text-signal',
  sell: 'text-warn',
  hold: 'text-muted',
}

export default function TickLog({ ticks }) {
  const recent = [...ticks].reverse().slice(0, 40)

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-line px-4 py-2.5">
        <h2 className="font-sans text-xs font-semibold uppercase tracking-wider text-muted">
          Strategy log
        </h2>
        <span className="font-mono text-2xs text-muted">{ticks.length} ticks</span>
      </div>
      <div className="flex-1 overflow-y-auto">
        {recent.length === 0 && (
          <div className="px-4 py-8 text-center font-mono text-xs text-muted">
            Waiting for first tick — start a bot to see live decisions here.
          </div>
        )}
        <table className="w-full font-mono text-xs">
          <tbody>
            {recent.map((t, i) => (
              <tr key={i} className="border-b border-line/50 hover:bg-panel2">
                <td className="whitespace-nowrap px-4 py-2 text-muted">
                  {new Date().toLocaleTimeString('en-US', { hour12: false })}
                </td>
                <td className="px-2 py-2 text-ink">{t.symbol}</td>
                <td className="px-2 py-2 text-ink tabular-nums">
                  {t.price?.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </td>
                <td className={`px-2 py-2 font-semibold uppercase ${SIGNAL_STYLES[t.signal] || 'text-muted'}`}>
                  {t.signal}
                </td>
                <td className="px-4 py-2 text-muted">{t.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
