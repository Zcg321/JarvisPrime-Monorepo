from src.reflex.core import Reflex
from src.reflex import ledger


def setup_ledger(tmp_path, monkeypatch):
    path = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(ledger, "LEDGER_PATH", path)
    return path


def test_stop_loss(monkeypatch, tmp_path):
    setup_ledger(tmp_path, monkeypatch)
    ledger.record(100, 0)
    r = Reflex()
    r.policy.update({"stop_loss_daily": 0.05, "unit_fraction": 1.0})
    res = r.self_check({"bankroll": 1000, "wager": 10, "affect": "calm"})
    assert res["blocked"] and res["reason"] == "stop_loss"


def test_stop_win(monkeypatch, tmp_path):
    setup_ledger(tmp_path, monkeypatch)
    ledger.record(100, 200)
    r = Reflex()
    r.policy.update({"stop_win_lock": 0.05, "unit_fraction": 1.0})
    res = r.self_check({"bankroll": 1000, "wager": 10, "affect": "calm"})
    assert res["blocked"] and res["reason"] == "stop_win"
