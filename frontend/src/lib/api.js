const BASE = '/api/v1'

async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${res.status})`)
  }
  return res.json()
}

export const api = {
  getPortfolio: (quoteAsset = 'USDT') =>
    fetch(`${BASE}/market/portfolio?quote_asset=${quoteAsset}`).then(handle),

  getTicker: (base, quote) =>
    fetch(`${BASE}/market/ticker/${base}/${quote}`).then(handle),

  listStrategies: () => fetch(`${BASE}/market/strategies`).then(handle),

  runBacktest: (payload) =>
    fetch(`${BASE}/backtest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(handle),
}
