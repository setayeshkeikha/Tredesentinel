from app.services.risk import RiskManager
from app.services.strategies.base import Signal, StrategyDecision


def test_risk_manager_halts_on_drawdown_breach():
    rm = RiskManager(max_daily_drawdown_pct=0.05)
    rm.check_drawdown(10_000.0)  # sets day-start equity
    assert not rm.is_halted

    rm.check_drawdown(9_400.0)  # 6% drawdown, exceeds 5% limit
    assert rm.is_halted
    assert "drawdown" in rm.halt_reason.lower()


def test_halted_risk_manager_rejects_all_signals():
    rm = RiskManager(max_daily_drawdown_pct=0.05)
    rm.check_drawdown(10_000.0)
    rm.check_drawdown(9_000.0)  # trips halt

    decision = StrategyDecision(Signal.BUY, "test buy signal", 1.0)
    result = rm.evaluate(decision, portfolio_value=9_000.0, current_price=100.0)
    assert result.approved is False


def test_position_sizing_respects_max_position_pct():
    rm = RiskManager(max_position_pct=0.10)
    decision = StrategyDecision(Signal.BUY, "test", confidence=1.0)
    result = rm.evaluate(decision, portfolio_value=10_000.0, current_price=100.0)
    assert result.approved is True
    # 10% of 10,000 = 1,000 notional / 100 price = 10 units
    assert abs(result.sized_amount - 10.0) < 0.01


def test_stop_loss_triggers_sell_approval():
    rm = RiskManager(stop_loss_pct=0.03)
    decision = StrategyDecision(Signal.SELL, "manual sell test", 1.0)
    result = rm.evaluate(
        decision, portfolio_value=10_000.0, current_price=94.0, position_entry_price=100.0
    )
    assert result.approved is True
    assert "stop-loss" in result.reason.lower()
