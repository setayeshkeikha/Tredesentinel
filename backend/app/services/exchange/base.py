"""
ExchangeAdapter is the seam between strategy logic and the outside world.

Every strategy and the RiskManager talk to this interface only. Whether
orders actually hit Binance or are simulated in-memory is decided once,
at startup, by which concrete class gets instantiated. This is what lets
paper trading and live trading share 100% of the decision-making code.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    FILLED = "filled"
    REJECTED = "rejected"
    PENDING = "pending"


@dataclass
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class OrderResult:
    order_id: str
    symbol: str
    side: OrderSide
    amount: float
    price: float
    status: OrderStatus
    timestamp: datetime
    fee: float = 0.0


@dataclass
class Balance:
    asset: str
    free: float
    locked: float


class ExchangeAdapter(ABC):
    """Common interface implemented by PaperExchange and LiveExchange."""

    @abstractmethod
    async def get_latest_price(self, symbol: str) -> float:
        ...

    @abstractmethod
    async def get_ohlcv(
        self, symbol: str, timeframe: str, limit: int = 200
    ) -> list[Candle]:
        ...

    @abstractmethod
    async def place_market_order(
        self, symbol: str, side: OrderSide, amount: float
    ) -> OrderResult:
        ...

    @abstractmethod
    async def get_balance(self, asset: str) -> Balance:
        ...

    @abstractmethod
    async def get_portfolio_value(self, quote_asset: str = "USDT") -> float:
        ...
