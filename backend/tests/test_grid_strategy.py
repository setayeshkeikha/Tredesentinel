from app.services.strategies.base import Signal
from app.services.strategies.grid_strategy import GridStrategy


def test_grid_holds_price_outside_range():
    from tests.conftest import make_candles

    strategy = GridStrategy(lower_bound=100, upper_bound=200, grid_levels=10)
    candles = make_candles([250.0] * 5)  # above upper_bound
    decision = strategy.decide(candles, position=None)
    assert decision.signal == Signal.HOLD
    assert "outside" in decision.reason.lower()


def test_grid_buys_at_grid_level_in_range():
    from tests.conftest import make_candles

    strategy = GridStrategy(lower_bound=100, upper_bound=200, grid_levels=10)
    candles = make_candles([150.0] * 5)
    decision = strategy.decide(candles, position=None)
    assert decision.signal == Signal.BUY
