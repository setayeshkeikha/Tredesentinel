from app.services.strategies.base import Signal
from app.services.strategies.rsi_strategy import RSIStrategy


def test_rsi_buys_when_oversold(oversold_candles):
    strategy = RSIStrategy(period=14, oversold=30, overbought=70)
    decision = strategy.decide(oversold_candles, position=None)
    assert decision.signal == Signal.BUY
    assert "oversold" in decision.reason


def test_rsi_holds_with_no_position_data():
    from tests.conftest import make_candles

    flat_candles = make_candles([100.0] * 20)
    strategy = RSIStrategy()
    decision = strategy.decide(flat_candles, position=None)
    assert decision.signal == Signal.HOLD


def test_rsi_does_not_buy_when_already_in_position(oversold_candles):
    from app.services.strategies.base import Position

    strategy = RSIStrategy()
    position = Position(symbol="BTC/USDT", amount=1.0, entry_price=100.0)
    decision = strategy.decide(oversold_candles, position=position)
    assert decision.signal != Signal.BUY
