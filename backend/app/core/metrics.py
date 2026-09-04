"""
Prometheus metrics exposed at GET /metrics (see main.py). These are the
numbers an on-call person actually needs at 3am: is the scheduler still
ticking, are trades still happening, has the risk circuit breaker tripped,
and how long are exchange calls taking.
"""
from prometheus_client import Counter, Gauge, Histogram

bot_ticks_total = Counter(
    "tradesentinel_bot_ticks_total",
    "Number of strategy ticks processed",
    ["bot_id", "symbol", "signal"],
)

trades_total = Counter(
    "tradesentinel_trades_total",
    "Number of trades executed",
    ["symbol", "side", "mode"],
)

trade_pnl = Histogram(
    "tradesentinel_trade_pnl",
    "Realized PnL per closed trade (quote currency)",
    ["symbol"],
    buckets=(-500, -100, -50, -10, 0, 10, 50, 100, 500, 1000),
)

risk_halts_total = Counter(
    "tradesentinel_risk_halts_total",
    "Number of times the drawdown circuit breaker has tripped",
    ["bot_id"],
)

portfolio_value = Gauge(
    "tradesentinel_portfolio_value",
    "Current portfolio value in quote currency",
    ["quote_asset", "mode"],
)

exchange_call_duration_seconds = Histogram(
    "tradesentinel_exchange_call_duration_seconds",
    "Latency of calls to the exchange adapter",
    ["method", "exchange_mode"],
)

active_bots = Gauge(
    "tradesentinel_active_bots",
    "Number of bots currently in RUNNING status",
)
