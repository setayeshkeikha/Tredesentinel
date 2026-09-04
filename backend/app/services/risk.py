"""
RiskManager sits between a strategy's decision and the exchange call.
A strategy can say BUY all it wants — RiskManager can still veto it,
resize it, or trip a circuit breaker that halts all trading for the bot
regardless of which strategy is asking. This separation means adding a
reckless new strategy can never bypass the account's risk limits.
"""
from dataclasses import dataclass, field
from datetime import date

from app.core.config import settings
from app.services.strategies.base import Signal, StrategyDecision


@dataclass
class RiskDecision:
    approved: bool
    reason: str
    sized_amount: float = 0.0


@dataclass
class RiskManager:
    max_position_pct: float = settings.MAX_POSITION_SIZE_PCT
    max_daily_drawdown_pct: float = settings.MAX_DAILY_DRAWDOWN_PCT
    stop_loss_pct: float = settings.DEFAULT_STOP_LOSS_PCT
    take_profit_pct: float = settings.DEFAULT_TAKE_PROFIT_PCT

    _day_start_equity: float | None = field(default=None, init=False)
    _current_day: date | None = field(default=None, init=False)
    _halted: bool = field(default=False, init=False)
    _halt_reason: str = field(default="", init=False)

    def _roll_day_if_needed(self, equity: float) -> None:
        today = date.today()
        if self._current_day != today:
            self._current_day = today
            self._day_start_equity = equity
            self._halted = False
            self._halt_reason = ""

    def check_drawdown(self, current_equity: float) -> None:
        """Call once per tick with current portfolio value. May trip the halt."""
        self._roll_day_if_needed(current_equity)
        if self._day_start_equity is None or self._day_start_equity == 0:
            return
        drawdown = (self._day_start_equity - current_equity) / self._day_start_equity
        if drawdown >= self.max_daily_drawdown_pct and not self._halted:
            self._halted = True
            self._halt_reason = (
                f"Daily drawdown {drawdown:.1%} breached limit "
                f"{self.max_daily_drawdown_pct:.1%} — trading halted until tomorrow"
            )

    @property
    def is_halted(self) -> bool:
        return self._halted

    @property
    def halt_reason(self) -> str:
        return self._halt_reason

    def evaluate(
        self,
        decision: StrategyDecision,
        portfolio_value: float,
        current_price: float,
        position_entry_price: float | None = None,
    ) -> RiskDecision:
        if self._halted:
            return RiskDecision(False, self._halt_reason)

        if decision.signal == Signal.HOLD:
            return RiskDecision(False, "Strategy signaled HOLD")

        if decision.signal == Signal.SELL and position_entry_price is not None:
            change = (current_price - position_entry_price) / position_entry_price
            if change <= -self.stop_loss_pct:
                return RiskDecision(True, f"Stop-loss triggered ({change:.1%})", 0.0)
            if change >= self.take_profit_pct:
                return RiskDecision(True, f"Take-profit triggered ({change:.1%})", 0.0)

        if decision.signal == Signal.BUY:
            max_notional = portfolio_value * self.max_position_pct * decision.confidence
            sized_amount = max_notional / current_price if current_price > 0 else 0.0
            if sized_amount <= 0:
                return RiskDecision(False, "Sized amount is zero")
            return RiskDecision(True, decision.reason, sized_amount)

        return RiskDecision(True, decision.reason)
