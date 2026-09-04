"""
PaperExchange simulates order execution against *real* market data.

We still pull live OHLCV/ticker data from a real exchange via ccxt's public
(no-auth) endpoints — only order placement is simulated. This means paper
trading results are a meaningful preview of live behavior, not a toy.
"""
import uuid
from datetime import datetime, timezone

import ccxt.async_support as ccxt

from app.services.exchange.base import (
    Balance,
    Candle,
    ExchangeAdapter,
    OrderResult,
    OrderSide,
    OrderStatus,
)


class PaperExchange(ExchangeAdapter):
    def __init__(self, exchange_name: str = "binance", starting_balance: float = 10_000.0):
        exchange_cls = getattr(ccxt, exchange_name)
        self._public_client = exchange_cls({"enableRateLimit": True})
        self._balances: dict[str, float] = {"USDT": starting_balance}
        self._fee_rate = 0.001  # 0.1%, typical spot taker fee

    async def close(self) -> None:
        await self._public_client.close()

    async def get_latest_price(self, symbol: str) -> float:
        ticker = await self._public_client.fetch_ticker(symbol)
        return float(ticker["last"])

    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 200) -> list[Candle]:
        raw = await self._public_client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
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
        price = await self.get_latest_price(symbol)
        base, quote = symbol.split("/")
        cost = amount * price
        fee = cost * self._fee_rate

        if side == OrderSide.BUY:
            if self._balances.get(quote, 0.0) < cost + fee:
                return OrderResult(
                    order_id=str(uuid.uuid4()),
                    symbol=symbol,
                    side=side,
                    amount=amount,
                    price=price,
                    status=OrderStatus.REJECTED,
                    timestamp=datetime.now(timezone.utc),
                )
            self._balances[quote] = self._balances.get(quote, 0.0) - cost - fee
            self._balances[base] = self._balances.get(base, 0.0) + amount
        else:
            if self._balances.get(base, 0.0) < amount:
                return OrderResult(
                    order_id=str(uuid.uuid4()),
                    symbol=symbol,
                    side=side,
                    amount=amount,
                    price=price,
                    status=OrderStatus.REJECTED,
                    timestamp=datetime.now(timezone.utc),
                )
            self._balances[base] = self._balances.get(base, 0.0) - amount
            self._balances[quote] = self._balances.get(quote, 0.0) + cost - fee

        return OrderResult(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            amount=amount,
            price=price,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(timezone.utc),
            fee=fee,
        )

    async def get_balance(self, asset: str) -> Balance:
        free = self._balances.get(asset, 0.0)
        return Balance(asset=asset, free=free, locked=0.0)

    async def get_portfolio_value(self, quote_asset: str = "USDT") -> float:
        total = self._balances.get(quote_asset, 0.0)
        for asset, amount in self._balances.items():
            if asset == quote_asset or amount == 0:
                continue
            try:
                price = await self.get_latest_price(f"{asset}/{quote_asset}")
                total += amount * price
            except Exception:
                continue
        return total
