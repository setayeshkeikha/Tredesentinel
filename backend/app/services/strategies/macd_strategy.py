from app.services.exchange.base import Candle
from app.services.strategies.base import BaseStrategy, Position, Signal, StrategyDecision


def _ema(values: list[float], period: int) -> list[float]:
    k = 2 / (period + 1)
    ema_values = [values[0]]
    for price in values[1:]:
        ema_values.append(price * k + ema_values[-1] * (1 - k))
    return ema_values


class MACDStrategy(BaseStrategy):
    """Trend-following: buy on bullish MACD/signal crossover, sell on bearish."""

    name = "macd"

    def __init__(self, fast: int = 12, slow: int = 26, signal_period: int = 9, **kwargs):
        super().__init__(fast=fast, slow=slow, signal_period=signal_period, **kwargs)
        self.fast = fast
        self.slow = slow
        self.signal_period = signal_period

    def decide(self, candles: list[Candle], position: Position | None) -> StrategyDecision:
        closes = [c.close for c in candles]
        min_needed = self.slow + self.signal_period
        if len(closes) < min_needed:
            return StrategyDecision(Signal.HOLD, f"Need {min_needed} candles, have {len(closes)}")

        fast_ema = _ema(closes, self.fast)
        slow_ema = _ema(closes, self.slow)
        macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]
        signal_line = _ema(macd_line, self.signal_period)

        macd_prev, macd_now = macd_line[-2], macd_line[-1]
        sig_prev, sig_now = signal_line[-2], signal_line[-1]

        bullish_cross = macd_prev <= sig_prev and macd_now > sig_now
        bearish_cross = macd_prev >= sig_prev and macd_now < sig_now

        if position is None and bullish_cross:
            return StrategyDecision(Signal.BUY, "MACD crossed above signal line", 0.9)
        if position is not None and bearish_cross:
            return StrategyDecision(Signal.SELL, "MACD crossed below signal line", 1.0)
        return StrategyDecision(Signal.HOLD, "No crossover")
