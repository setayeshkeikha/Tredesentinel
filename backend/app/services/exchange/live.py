"""
LiveExchange places real orders via ccxt against an authenticated exchange
account. This class deliberately contains almost no logic of its own —
all strategy/risk decisions happen upstream. That asymmetry (dumb execution
layer, smart decision layer) is what makes it safe to test decision logic
in PaperExchange and trust it will behave the same way here.
"""
from datetime import datetime, timezone

import ccxt.async_support as ccxt

from app.core.config import settings
from app.services.exchange.base import (
    Balance,
    Candle,
    ExchangeAdapter,
    OrderResult,
    OrderSide,
    OrderStatus,
)


class LiveExchange(ExchangeAdapter):
    def __init__(self):
        exchange_cls = getattr(ccxt, settings.EXCHANGE_NAME)
        self._client = exchange_cls(
            {
                "apiKey": settings.EXCHANGE_API_KEY,
                "secret": settings.EXCHANGE_API_SECRET,
                "enableRateLimit": True,
            }
        )
        if settings.EXCHANGE_SANDBOX and self._client.urls.get("test"):
            self._client.set_sandbox_mode(True)

    async def close(self) -> None:
        await self._client.close()

    async def get_latest_price(self, symbol: str) -> float:
        ticker = await self._client.fetch_ticker(symbol)
        return float(ticker["last"])

    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 200) -> list[Candle]:
        raw = await self._client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        return [
            Candle(
                timestamp=datetime.fromtimestamp(row[0] / 1000, tz=timezone.utc),
                open=row[1],
                high=row[2],
                low=row[3],
                close=row[4],
                volume=row[5],
            )
            for row in raw
        ]

    async def place_market_order(self, symbol: str, side: OrderSide, amount: float) -> OrderResult:
        try:
            order = await self._client.create_order(
                symbol=symbol, type="market", side=side.value, amount=amount
            )
            return OrderResult(
                order_id=str(order["id"]),
                symbol=symbol,
                side=side,
                amount=float(order.get("filled", amount)),
                price=float(order.get("average") or order.get("price") or 0.0),
                status=OrderStatus.FILLED,
                timestamp=datetime.now(timezone.utc),
                fee=float((order.get("fee") or {}).get("cost", 0.0)),
            )
        except Exception:
            return OrderResult(
                order_id="rejected",
                symbol=symbol,
                side=side,
                amount=amount,
                price=0.0,
                status=OrderStatus.REJECTED,
                timestamp=datetime.now(timezone.utc),
            )

    async def get_balance(self, asset: str) -> Balance:
        bal = await self._client.fetch_balance()
        info = bal.get(asset, {"free": 0.0, "used": 0.0})
        return Balance(asset=asset, free=float(info.get("free", 0.0)), locked=float(info.get("used", 0.0)))

    async def get_portfolio_value(self, quote_asset: str = "USDT") -> float:
        bal = await self._client.fetch_balance()
        total = float(bal.get(quote_asset, {}).get("total", 0.0))
        for asset, info in bal.get("total", {}).items() if isinstance(bal.get("total"), dict) else []:
            if asset == quote_asset or not info:
                continue
            try:
                price = await self.get_latest_price(f"{asset}/{quote_asset}")
                total += info * price
            except Exception:
                continue
        return total
