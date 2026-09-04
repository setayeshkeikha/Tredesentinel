import pytest
from datetime import datetime, timedelta, timezone

from app.services.exchange.base import Candle


def make_candles(closes: list[float], start_price_open: float | None = None) -> list[Candle]:
    """Helper to build a simple candle series from a list of close prices."""
    candles = []
    ts = datetime.now(timezone.utc) - timedelta(hours=len(closes))
    prev_close = start_price_open if start_price_open is not None else closes[0]
    for close in closes:
        candles.append(
            Candle(
                timestamp=ts,
                open=prev_close,
                high=max(prev_close, close) * 1.001,
                low=min(prev_close, close) * 0.999,
                close=close,
                volume=100.0,
            )
        )
        prev_close = close
        ts += timedelta(hours=1)
    return candles


@pytest.fixture
def uptrend_candles():
    # Monotonic uptrend, good for MACD bullish crossover tests
    return make_candles([100 + i * 0.5 for i in range(80)])


@pytest.fixture
def oversold_candles():
    # Sharp drop then flat, should push RSI below 30
    prices = [100.0] * 5 + [100 - i * 2 for i in range(1, 16)]
    return make_candles(prices)
