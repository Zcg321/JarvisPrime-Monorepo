from src.tools.submit_plan import submit_plan
from src.reflex import core


def test_submit_plan_deterministic(monkeypatch):
    lineups = [{} for _ in range(10)]
    res1 = submit_plan("SLATE", lineups, bankroll=100, entry_fee=5.0, max_entries=20)
    res2 = submit_plan("SLATE", lineups, bankroll=100, entry_fee=5.0, max_entries=20)
    assert res1 == res2


def test_submit_plan_blocked(monkeypatch):
    monkeypatch.setitem(core.RISK, 'require_ev_ge', 0.1)
    lineups = [{}]
    res = submit_plan("SLATE", lineups, bankroll=100, entry_fee=1.0, max_entries=1)
    assert res['blocked'] is True
    assert 'reason' in res
