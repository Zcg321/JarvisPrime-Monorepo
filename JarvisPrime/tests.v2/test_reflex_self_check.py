import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.reflex.core import Reflex


def test_self_check_bankroll_and_safety():
    r = Reflex()
    decision = {
        "bankroll": 100,
        "wager": 10,
        "risk": 0,
        "risk_limit": 1,
        "needs_tool": True,
        "uses_local": True,
    }
    check = r.self_check(decision)
    assert check["bankroll_ok"] and check["safety_ok"]

    bad = {
        "bankroll": 5,
        "wager": 10,
        "risk": 0,
        "risk_limit": 1,
        "danger": True,
        "needs_tool": False,
        "uses_local": True,
    }
    check_bad = r.self_check(bad)
    assert not check_bad["bankroll_ok"]
    assert not check_bad["safety_ok"]

