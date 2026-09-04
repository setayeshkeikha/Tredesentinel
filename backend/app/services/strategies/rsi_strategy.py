from app.services.exchange.base import Candle
from app.services.strategies.base import BaseStrategy, Position, Signal, StrategyDecision


def _compute_rsi(closes: list[float], period: int) -> float:
    if len(closes) < period + 1:
        return 50.0  # neutral if not enough data
    gains, losses = [], []
    for i in range(-period, 0):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


class RSIStrategy(BaseStrategy):
    """Classic mean-reversion: buy oversold, sell overbought."""

    name = "rsi"

    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70, **kwargs):
        super().__init__(period=period, oversold=oversold, overbought=overbought, **kwargs)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def decide(self, candles: list[Candle], position: Position | None) -> StrategyDecision:
        closes = [c.close for c in candles]
        rsi = _compute_rsi(closes, self.period)

        if position is None and rsi <= self.oversold:
            confidence = min(1.0, (self.oversold - rsi) / self.oversold + 0.5)
            return StrategyDecision(Signal.BUY, f"RSI {rsi:.1f} <= oversold {self.oversold}", confidence)

        if position is not None and rsi >= self.overbought:
            return StrategyDecision(Signal.SELL, f"RSI {rsi:.1f} >= overbought {self.overbought}", 1.0)

        return StrategyDecision(Signal.HOLD, f"RSI {rsi:.1f} in neutral zone")
