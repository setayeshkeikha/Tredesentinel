from app.services.exchange.base import Candle
from app.services.strategies.base import BaseStrategy, Position, Signal, StrategyDecision


class GridStrategy(BaseStrategy):
    """
    Range-bound strategy: places a virtual grid of price levels between
    lower_bound and upper_bound. Buys when price drops to a grid line below
    the entry, sells when it rises to a grid line above. Suited to sideways
    markets rather than strong trends.
    """

    name = "grid"

    def __init__(
        self, lower_bound: float, upper_bound: float, grid_levels: int = 10, **kwargs
    ):
        super().__init__(
            lower_bound=lower_bound, upper_bound=upper_bound, grid_levels=grid_levels, **kwargs
        )
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.grid_levels = grid_levels
        step = (upper_bound - lower_bound) / grid_levels
        self._levels = [lower_bound + i * step for i in range(grid_levels + 1)]

    def _nearest_level_below(self, price: float) -> float | None:
        below = [lvl for lvl in self._levels if lvl <= price]
        return max(below) if below else None

    def decide(self, candles: list[Candle], position: Position | None) -> StrategyDecision:
        price = candles[-1].close

        if price < self.lower_bound or price > self.upper_bound:
            return StrategyDecision(Signal.HOLD, "Price outside grid range")

        level = self._nearest_level_below(price)

        if position is None and level is not None:
            return StrategyDecision(Signal.BUY, f"Price {price:.2f} at grid level {level:.2f}", 0.6)

        if position is not None:
            step = (self.upper_bound - self.lower_bound) / self.grid_levels
            target = position.entry_price + step
            if price >= target:
                return StrategyDecision(Signal.SELL, f"Price {price:.2f} reached grid target {target:.2f}", 1.0)

        return StrategyDecision(Signal.HOLD, "Waiting for next grid level")
