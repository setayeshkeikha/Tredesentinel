"""
Every strategy answers one question: given recent candles and the current
position (if any), what should happen next? Nothing else. Strategies never
touch the exchange, never manage risk sizing, never send notifications —
that separation is what lets the same class run in backtest, paper, and
live modes unmodified.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from app.services.exchange.base import Candle


class Signal(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Position:
    symbol: str
    amount: float
    entry_price: float


@dataclass
class StrategyDecision:
    signal: Signal
    reason: str
    confidence: float = 1.0  # 0-1, lets risk manager scale position size


class BaseStrategy(ABC):
    name: str = "base"

    def __init__(self, **params):
        self.params = params

    @abstractmethod
    def decide(self, candles: list[Candle], position: Position | None) -> StrategyDecision:
        """candles are ordered oldest -> newest; candles[-1] is the current bar."""
        ...
