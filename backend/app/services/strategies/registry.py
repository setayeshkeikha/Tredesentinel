"""
Registering a new strategy means adding one line here. The API, backtester,
and live workers all resolve strategies through this registry by name, so
none of them need to change when a new strategy is added.
"""
from app.services.strategies.base import BaseStrategy
from app.services.strategies.grid_strategy import GridStrategy
from app.services.strategies.macd_strategy import MACDStrategy
from app.services.strategies.rsi_strategy import RSIStrategy

STRATEGY_REGISTRY: dict[str, type[BaseStrategy]] = {
    RSIStrategy.name: RSIStrategy,
    MACDStrategy.name: MACDStrategy,
    GridStrategy.name: GridStrategy,
}


def create_strategy(name: str, **params) -> BaseStrategy:
    if name not in STRATEGY_REGISTRY:
        available = ", ".join(STRATEGY_REGISTRY.keys())
        raise ValueError(f"Unknown strategy '{name}'. Available: {available}")
    return STRATEGY_REGISTRY[name](**params)
