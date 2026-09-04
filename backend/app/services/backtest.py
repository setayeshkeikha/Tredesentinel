"""
Runs a strategy against historical candles using the exact same
BaseStrategy.decide() and RiskManager.evaluate() code paths used in live
and paper trading. This is the guarantee that a backtest result actually
predicts live behavior instead of being a parallel simulation that can
silently diverge from production logic.
"""
from dataclasses import dataclass, field

from app.services.exchange.base import Candle
from app.services.risk import RiskManager
from app.services.strategies.base import BaseStrategy, Position, Signal


@dataclass
class BacktestTrade:
    timestamp: str
    side: str
    price: float
    amount: float
    reason: str
    pnl: float | None = None


@dataclass
class BacktestReport:
    starting_equity: float
    ending_equity: float
    total_trades: int
    win_rate: float
    max_drawdown_pct: float
    equity_curve: list[dict] = field(default_factory=list)
    trades: list[BacktestTrade] = field(default_factory=list)


def run_backtest(
    candles: list[Candle],
    strategy: BaseStrategy,
    starting_equity: float = 10_000.0,
    lookback: int = 50,
    risk_manager: RiskManager | None = None,
) -> BacktestReport:
    risk_manager = risk_manager or RiskManager()

    cash = starting_equity
    position: Position | None = None
    trades: list[BacktestTrade] = []
    equity_curve: list[dict] = []
    peak_equity = starting_equity
    max_drawdown = 0.0

    for i in range(lookback, len(candles)):
        window = candles[max(0, i - lookback) : i + 1]
        current = window[-1]

        equity = cash if position is None else cash + position.amount * current.close
        risk_manager.check_drawdown(equity)

        decision = strategy.decide(window, position)
        risk_result = risk_manager.evaluate(
            decision,
            portfolio_value=equity,
            current_price=current.close,
            position_entry_price=position.entry_price if position else None,
        )

        if risk_result.approved and decision.signal == Signal.BUY and position is None:
            amount = risk_result.sized_amount
            cost = amount * current.close
            if cost <= cash and amount > 0:
                cash -= cost
                position = Position(symbol="", amount=amount, entry_price=current.close)
                trades.append(
                    BacktestTrade(
                        timestamp=current.timestamp.isoformat(),
                        side="buy",
                        price=current.close,
                        amount=amount,
                        reason=decision.reason,
                    )
                )

        elif risk_result.approved and decision.signal == Signal.SELL and position is not None:
            proceeds = position.amount * current.close
            pnl = proceeds - (position.amount * position.entry_price)
            cash += proceeds
            trades.append(
                BacktestTrade(
                    timestamp=current.timestamp.isoformat(),
                    side="sell",
                    price=current.close,
                    amount=position.amount,
                    reason=decision.reason,
                    pnl=pnl,
                )
            )
            position = None

        equity = cash if position is None else cash + position.amount * current.close
        peak_equity = max(peak_equity, equity)
        drawdown = (peak_equity - equity) / peak_equity if peak_equity > 0 else 0
        max_drawdown = max(max_drawdown, drawdown)
        equity_curve.append({"t": current.timestamp.isoformat(), "equity": round(equity, 2)})

    final_equity = cash if position is None else cash + position.amount * candles[-1].close
    sell_trades = [t for t in trades if t.side == "sell"]
    wins = [t for t in sell_trades if (t.pnl or 0) > 0]
    win_rate = len(wins) / len(sell_trades) if sell_trades else 0.0

    return BacktestReport(
        starting_equity=starting_equity,
        ending_equity=round(final_equity, 2),
        total_trades=len(trades),
        win_rate=round(win_rate, 4),
        max_drawdown_pct=round(max_drawdown, 4),
        equity_curve=equity_curve,
        trades=trades,
    )
