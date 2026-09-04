from functools import lru_cache

from app.core.config import settings
from app.services.exchange.base import ExchangeAdapter
from app.services.exchange.live import LiveExchange
from app.services.exchange.paper import PaperExchange


@lru_cache
def get_exchange() -> ExchangeAdapter:
    """Single source of truth for which exchange implementation is active.

    Everything downstream (strategies, risk manager, API routes) depends on
    ExchangeAdapter, never on PaperExchange/LiveExchange directly, so
    flipping TRADING_MODE in .env is the only change needed to go live.
    """
    if settings.TRADING_MODE == "live":
        return LiveExchange()
    return PaperExchange(exchange_name=settings.EXCHANGE_NAME)
