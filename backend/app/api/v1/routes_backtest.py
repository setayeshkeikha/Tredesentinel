import math
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

from app.schemas.schemas import BacktestRequest, BacktestResponse
from app.services.backtest import run_backtest
from app.services.strategies.registry import create_strategy
from app.services.exchange.base import Candle


router = APIRouter(prefix="/backtest", tags=["backtest"])


def generate_demo_candles(limit: int = 500) -> list[Candle]:
    candles = []

    start = datetime.now(timezone.utc) - timedelta(hours=limit)

    price = 60000.0

    for i in range(limit):
        trend = i * 8
        wave = math.sin(i / 12) * 900
        wave2 = math.sin(i / 35) * 1400

        close = price + trend + wave + wave2

        open_price = close - math.sin(i) * 150
        high = max(open_price, close) + 120
        low = min(open_price, close) - 120

        candles.append(
            Candle(
                timestamp=start + timedelta(hours=i),
                open=float(open_price),
                high=float(high),
                low=float(low),
                close=float(close),
                volume=1000.0,
            )
        )

    return candles


@router.post("", response_model=BacktestResponse)
async def backtest(payload: BacktestRequest):

    try:
        strategy = create_strategy(
            payload.strategy_name,
            **payload.strategy_params
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    candles = generate_demo_candles(payload.candle_limit)

    if len(candles) < 60:
        raise HTTPException(
            status_code=400,
            detail="Not enough historical data returned for this symbol/timeframe"
        )

    report = run_backtest(
        candles,
        strategy,
        starting_equity=payload.starting_equity
    )

    return BacktestResponse(
        starting_equity=report.starting_equity,
        ending_equity=report.ending_equity,
        total_trades=report.total_trades,
        win_rate=report.win_rate,
        max_drawdown_pct=report.max_drawdown_pct,
        equity_curve=report.equity_curve,
        trades=[
            {
                "timestamp": t.timestamp,
                "side": t.side,
                "price": t.price,
                "amount": t.amount,
                "reason": t.reason,
                "pnl": t.pnl,
            }
            for t in report.trades
        ],
    )
