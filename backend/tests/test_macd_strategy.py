from app.services.strategies.base import Signal
from app.services.strategies.macd_strategy import MACDStrategy


def test_macd_holds_with_insufficient_data():
    from tests.conftest import make_candles

    short_candles = make_candles([100.0] * 10)
    strategy = MACDStrategy()
    decision = strategy.decide(short_candles, position=None)
    assert decision.signal == Signal.HOLD
    assert "Need" in decision.reason


def test_macd_can_signal_on_uptrend(uptrend_candles):
    strategy = MACDStrategy(fast=5, slow=13, signal_period=4)
    decision = strategy.decide(uptrend_candles, position=None)
    # On a steady uptrend from flat start, MACD should cross bullish at some point
    assert decision.signal in (Signal.BUY, Signal.HOLD)
