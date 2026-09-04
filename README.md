# TradeSentinel

A production-grade crypto trading bot platform — strategy backtesting, paper trading, and live execution, wrapped in a real-time terminal-style dashboard.

Built to demonstrate: async Python architecture, exchange integration (ccxt), WebSocket streaming, background task orchestration, and a distinctive frontend — not another CRUD boilerplate.

## Why this isn't "just another trading bot repo"

Most portfolio trading-bot projects are single-file scripts that print buy/sell signals to a terminal. TradeSentinel is architected as an actual platform:

- **Strategy engine is pluggable.** Strategies (RSI, MACD crossover, Grid) implement a common interface and are registered at runtime — adding a new strategy means writing one class, not touching the core engine.
- **Paper trading and live trading share the same code path.** The `ExchangeAdapter` interface has a `PaperExchange` implementation (simulated fills against real market data) and a `LiveExchange` implementation (ccxt against Binance/KuCoin). Strategies and risk management don't know or care which one is active.
- **Risk management is a first-class module**, not scattered `if` statements — position sizing, stop-loss/take-profit, and max-drawdown circuit breakers all run through one `RiskManager` that can halt trading independently of any strategy's own logic.
- **Backtesting uses the exact same strategy + risk code as live trading**, against historical OHLCV data, so results aren't a separate simulation that can drift from production behavior.
- **Bots are real, persisted, multi-tenant resources.** Each user registers, authenticates via JWT, and owns their own set of bots. Starting/pausing/stopping a bot is an API call — the scheduler worker polls Postgres every 15s and reconciles its running jobs to match, so changes take effect without a worker restart.
- **Open positions are derived from the trade ledger**, not tracked in a parallel mutable table. A worker crash or redeploy can't desync "what we think we're holding" from "what actually happened" — there's only one source of truth.
- **Auth uses a real access/refresh token pair**, not one long-lived JWT. Access tokens expire in 30 minutes; refresh tokens are persisted server-side so `/auth/logout` can revoke all of a user's sessions, and each token type is rejected if presented as the other even though both share a signing secret.
- **Every trade, tick, and risk halt is observable**: structured JSON logs (in prod) and Prometheus metrics (`/metrics`) covering tick counts, trade counts, realized PnL, risk-circuit-breaker trips, and live portfolio value — the kind of instrumentation an actual on-call rotation would need, not just print statements.

## Architecture

```
tradebot/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST + WebSocket routes (auth, bots, market, backtest, ws)
│   │   ├── core/            # config, security.py (JWT + password hashing), logging_config.py, metrics.py
│   │   ├── db/              # async session factory
│   │   ├── models/          # SQLAlchemy ORM models (User, RefreshToken, Bot, Trade, BacktestResult)
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── exchange/    # ExchangeAdapter, PaperExchange, LiveExchange (ccxt)
│   │   │   ├── strategies/  # BaseStrategy + RSI, MACD, Grid implementations
│   │   │   ├── risk.py      # RiskManager (stop-loss, drawdown circuit breaker)
│   │   │   ├── backtest.py  # Backtest engine (reuses strategy+risk code)
│   │   │   └── notifier.py  # Telegram / KavehNegar SMS alerts
│   │   └── workers/
│   │       ├── strategy_runner.py  # single-bot tick: decide -> risk-check -> execute -> log -> emit metrics
│   │       └── scheduler.py        # APScheduler process; reconciles jobs against active bots in Postgres
│   ├── alembic/             # migrations: 0001 (initial schema), 0002 (refresh_tokens + bot status)
│   └── tests/               # unit tests (strategies, risk, security) + integration tests (bot lifecycle, marked `integration`)
└── frontend/                 # React + Vite terminal-style dashboard
```

## Stack

- **Backend:** FastAPI (async), PostgreSQL + SQLAlchemy 2.0 (async), Redis (price cache + pub/sub for WebSocket fan-out), Alembic
- **Exchange integration:** ccxt (Binance, KuCoin — swappable)
- **Background execution:** APScheduler (strategy ticks), Celery optional for heavier backtests
- **Realtime:** native FastAPI WebSockets, Redis pub/sub to fan out to multiple connected clients
- **Notifications:** Telegram Bot API, KavehNegar SMS (Iran-accessible)
- **Frontend:** React + Vite, TailwindCSS, lightweight-charts (TradingView's OSS charting lib), JetBrains Mono for data
- **Testing:** Pytest + pytest-asyncio
- **Infra:** Docker Compose (api, worker, postgres, redis, frontend)

## Security model

- Passwords hashed with bcrypt (passlib); never stored or logged in plaintext.
- JWT access tokens (30 min expiry) authenticate every request. JWT refresh tokens (30 day expiry) are the only way to mint a new access token, carry a `type` claim, and are rejected if presented as an access token even though both share a signing secret.
- Refresh tokens are persisted in Postgres so `POST /auth/logout` can revoke all of a user's outstanding sessions server-side.
- Every bot route enforces ownership (`_get_owned_bot`) and returns 404 — not 403 — for another user's bot, so bot existence is never leaked.
- The `RiskManager` drawdown circuit breaker is enforced identically in paper and live mode; no strategy can bypass it, since the breaker lives outside strategy code entirely.

## Observability

- `GET /health` — liveness check.
- `GET /metrics` — Prometheus scrape endpoint: tick counts, trade counts, a realized-PnL histogram, a risk-halt counter, live portfolio value, and active bot count.
- JSON-structured logs when `ENV=prod` (human-readable console logs in `dev`); every HTTP response carries an `X-Request-ID` header for correlating a user-reported error to exact log lines.
- Every trade execution and every risk-circuit-breaker trip logs full context (`bot_id`, `symbol`, `price`, `amount`, `pnl`/`reason`) via `extra=` fields, not string interpolation, so it's directly queryable in any JSON log backend.

## Quick start

```bash
cp backend/.env.example backend/.env
docker-compose up --build
```

This brings up Postgres and Redis, runs Alembic migrations via a one-shot `migrate` service, then starts the API, the scheduler worker, and the frontend.

- API: http://localhost:8000 (docs at `/docs`)
- Dashboard: http://localhost:5173
- Default mode: **paper trading** — no real exchange keys required to try it.

### Creating your first bot

```bash
# Register and log in
curl -X POST localhost:8000/api/v1/auth/register -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"a-strong-password"}'

curl -X POST localhost:8000/api/v1/auth/login \
  -d "username=you@example.com&password=a-strong-password"
# -> { "access_token": "...", "refresh_token": "...", "token_type": "bearer" }

# Create and start a bot (paper trading by default)
curl -X POST localhost:8000/api/v1/bots -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"BTC RSI","symbol":"BTC/USDT","timeframe":"1h","strategy_name":"rsi","strategy_params":{"period":14,"oversold":30,"overbought":70}}'

curl -X POST localhost:8000/api/v1/bots/<bot_id>/start -H "Authorization: Bearer <access_token>"

# Pause without losing position/state, resume later
curl -X POST localhost:8000/api/v1/bots/<bot_id>/pause -H "Authorization: Bearer <access_token>"
curl -X POST localhost:8000/api/v1/bots/<bot_id>/start -H "Authorization: Bearer <access_token>"

# When the access token expires, get a new one without logging in again
curl -X POST localhost:8000/api/v1/auth/refresh -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'
```

The scheduler worker polls for active bots every 15 seconds and starts ticking them automatically — no worker restart needed.

## Running tests

```bash
make test              # fast unit tests: strategies, risk manager, JWT logic — no DB needed
make test-integration   # bot lifecycle + ownership tests against the real docker-compose stack
make test-all           # everything
```

## Database migrations

```bash
make migrate                          # apply all pending migrations
make revision msg="add something new" # generate a new migration from model changes
```

## Switching to live trading

Set in `.env`:
```
TRADING_MODE=live
EXCHANGE_NAME=binance
EXCHANGE_API_KEY=...
EXCHANGE_API_SECRET=...
```
The `RiskManager` circuit breaker (`MAX_DAILY_DRAWDOWN_PCT`) is active regardless of mode — live trading auto-halts if breached.

## License

MIT
