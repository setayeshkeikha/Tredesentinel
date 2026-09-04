from fastapi import APIRouter, HTTPException

from app.schemas.schemas import BacktestRequest, BacktestResponse
from app.services.backtest import run_backtest
from app.services.exchange.factory import get_exchange
from app.services.strategies.registry import create_strategy

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.post("", response_model=BacktestResponse)
async def backtest(payload: BacktestRequest):
    exchange = get_exchange()
    try:
        strategy = create_strategy(payload.strategy_name, **payload.strategy_params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    candles = await exchange.get_ohlcv(payload.symbol, payload.timeframe, limit=payload.candle_limit)
    if len(candles) < 60:
        raise HTTPException(status_code=400, detail="Not enough historical data returned for this symbol/timeframe")

    report = run_backtest(candles, strategy, starting_equity=payload.starting_equity)
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
