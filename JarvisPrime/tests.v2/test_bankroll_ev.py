from src.tools import bankroll_ev
from src.reflex import policy as risk_policy
import pytest


def test_bankroll_ev_plan_deterministic():
    risk_policy.set_token("user1")
    contests = [{"slate_id": "S1", "type": "classic", "entry_fee": 10.0, "max_entries": 3, "iters": 1000}]
    out1 = bankroll_ev.optimize(100.0, contests, seed=123)
    out2 = bankroll_ev.optimize(100.0, contests, seed=123)
    assert out1 == out2
    spend = sum(p["spend"] for p in out1["plan"])
    assert spend <= 100.0


def test_bankroll_ev_risk_guard():
    risk_policy.set_token("user1")
    contests = [{"slate_id": "S1", "type": "classic", "entry_fee": 10.0, "max_entries": 3, "iters": 10}]
    with pytest.raises(risk_policy.RiskViolation):
        bankroll_ev.optimize(100.0, contests, drawdown_guard_p95=0.0, seed=1)
