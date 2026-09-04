from fastapi import APIRouter

from app.core.config import settings
from app.schemas.schemas import PortfolioOut, TickerOut
from app.services.exchange.factory import get_exchange
from app.services.strategies.registry import STRATEGY_REGISTRY

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/ticker/{base}/{quote}", response_model=TickerOut)
async def get_ticker(base: str, quote: str):
    exchange = get_exchange()
    symbol = f"{base.upper()}/{quote.upper()}"
    price = await exchange.get_latest_price(symbol)
    return TickerOut(symbol=symbol, price=price)


@router.get("/portfolio", response_model=PortfolioOut)
async def get_portfolio(quote_asset: str = "USDT"):
    exchange = get_exchange()
    value = await exchange.get_portfolio_value(quote_asset)
    return PortfolioOut(quote_asset=quote_asset, total_value=round(value, 2), mode=settings.TRADING_MODE)


@router.get("/strategies")
async def list_strategies():
    return {"strategies": list(STRATEGY_REGISTRY.keys())}
