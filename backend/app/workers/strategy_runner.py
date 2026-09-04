"""
The scheduler tick loop: fetch candles -> ask the strategy -> pass through
risk management -> execute via whichever ExchangeAdapter is active -> log
the trade to Postgres -> publish a tick to the dashboard -> notify. Every
step after "ask the strategy" runs unchanged whether TRADING_MODE is
paper or live.

Open positions are derived from the Trade table on every tick rather than
kept in a process-local dict, so a worker restart doesn't silently forget
an open position.
"""
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.ws_manager import manager as ws_manager
from app.core.config import settings
from app.core.metrics import bot_ticks_total, portfolio_value as portfolio_value_gauge, risk_halts_total, trade_pnl, trades_total
from app.db.session import SessionLocal
from app.models.models import Trade
from app.services.exchange.base import OrderSide, Signal
from app.services.exchange.factory import get_exchange
from app.services.notifier import notify_halt, notify_trade
from app.services.risk import RiskManager
from app.services.strategies.base import Position
from app.services.strategies.registry import create_strategy

logger = logging.getLogger("tradesentinel.worker")

# RiskManager holds only same-process, same-day drawdown bookkeeping, which
# is safe to keep in memory (it resets daily regardless); trades and open
# positions themselves are the durable source of truth in Postgres.
_risk_managers: dict[str, RiskManager] = {}


async def _get_open_position(bot_id: uuid.UUID, symbol: str, db: AsyncSession) -> Position | None:
    """A position is open if the most recent trade for this bot+symbol was a BUY."""
    result = await db.execute(
        select(Trade)
        .where(Trade.bot_id == bot_id, Trade.symbol == symbol)
        .order_by(Trade.executed_at.desc())
        .limit(1)
    )
    last_trade = result.scalar_one_or_none()
    if last_trade is None or last_trade.side != "buy":
        return None
    return Position(symbol=symbol, amount=last_trade.amount, entry_price=last_trade.price)


async def _record_trade(
    bot_id: uuid.UUID,
    symbol: str,
    side: str,
    amount: float,
    price: float,
    fee: float,
    reason: str,
    pnl: float | None,
    db: AsyncSession,
) -> None:
    trade = Trade(
        bot_id=bot_id, symbol=symbol, side=side, amount=amount, price=price, fee=fee, reason=reason, pnl=pnl
    )
    db.add(trade)
    await db.commit()


async def run_bot_tick(bot_id: str, symbol: str, timeframe: str, strategy_name: str, strategy_params: dict) -> None:
    bot_uuid = bot_id if isinstance(bot_id, uuid.UUID) else uuid.UUID(bot_id)
    exchange = get_exchange()
    strategy = create_strategy(strategy_name, **strategy_params)
    risk_manager = _risk_managers.setdefault(str(bot_id), RiskManager())

    async with SessionLocal() as db:
        position = await _get_open_position(bot_uuid, symbol, db)

        candles = await exchange.get_ohlcv(symbol, timeframe, limit=200)
        if not candles:
            return

        portfolio_value = await exchange.get_portfolio_value()
        portfolio_value_gauge.labels(quote_asset="USDT", mode=settings.TRADING_MODE).set(portfolio_value)
        was_halted = risk_manager.is_halted
        risk_manager.check_drawdown(portfolio_value)

        if risk_manager.is_halted:
            if not was_halted:
                risk_halts_total.labels(bot_id=str(bot_id)).inc()
                logger.warning(
                    "Risk circuit breaker tripped", extra={"bot_id": str(bot_id), "reason": risk_manager.halt_reason}
                )
            await notify_halt(risk_manager.halt_reason)
            await ws_manager.publish_tick({"type": "halt", "bot_id": str(bot_id), "reason": risk_manager.halt_reason})
            return

        decision = strategy.decide(candles, position)
        current_price = candles[-1].close

        risk_result = risk_manager.evaluate(
            decision,
            portfolio_value=portfolio_value,
            current_price=current_price,
            position_entry_price=position.entry_price if position else None,
        )

        tick_payload = {
            "type": "tick",
            "bot_id": str(bot_id),
            "symbol": symbol,
            "price": current_price,
            "signal": decision.signal.value,
            "reason": decision.reason,
            "portfolio_value": round(portfolio_value, 2),
        }
        bot_ticks_total.labels(bot_id=str(bot_id), symbol=symbol, signal=decision.signal.value).inc()

        if risk_result.approved and decision.signal == Signal.BUY and position is None:
            result = await exchange.place_market_order(symbol, OrderSide.BUY, risk_result.sized_amount)
            if result.status.value == "filled":
                await _record_trade(
                    bot_uuid, symbol, "buy", result.amount, result.price, result.fee, risk_result.reason, None, db
                )
                trades_total.labels(symbol=symbol, side="buy", mode=settings.TRADING_MODE).inc()
                logger.info(
                    "Trade executed",
                    extra={"bot_id": str(bot_id), "symbol": symbol, "side": "buy", "price": result.price, "amount": result.amount},
                )
                await notify_trade(symbol, "buy", result.amount, result.price, risk_result.reason)
                tick_payload["trade"] = {"side": "buy", "amount": result.amount, "price": result.price}

        elif risk_result.approved and decision.signal == Signal.SELL and position is not None:
            result = await exchange.place_market_order(symbol, OrderSide.SELL, position.amount)
            if result.status.value == "filled":
                pnl = (result.price - position.entry_price) * position.amount - result.fee
                await _record_trade(
                    bot_uuid, symbol, "sell", result.amount, result.price, result.fee, risk_result.reason, pnl, db
                )
                trades_total.labels(symbol=symbol, side="sell", mode=settings.TRADING_MODE).inc()
                trade_pnl.labels(symbol=symbol).observe(pnl)
                logger.info(
                    "Trade executed",
                    extra={"bot_id": str(bot_id), "symbol": symbol, "side": "sell", "price": result.price, "amount": result.amount, "pnl": pnl},
                )
                await notify_trade(symbol, "sell", result.amount, result.price, risk_result.reason)
                tick_payload["trade"] = {"side": "sell", "amount": result.amount, "price": result.price}

        await ws_manager.publish_tick(tick_payload)
