from src.reflex.core import Reflex


def test_risk_gate_blocks():
    r = Reflex()
    decision = {"bankroll": 100, "wager": 1, "affect": "calm", "risk_stats": {"ev": -1, "variance": 3, "drawdown_p95": 0.3}}
    out = r.self_check(decision)
    assert out["blocked"]


def test_risk_gate_pass():
    r = Reflex()
    decision = {"bankroll": 100, "wager": 1, "affect": "calm", "risk_stats": {"ev": 1, "variance": 1, "drawdown_p95": 0.1}}
    out = r.self_check(decision)
    assert not out["blocked"]
