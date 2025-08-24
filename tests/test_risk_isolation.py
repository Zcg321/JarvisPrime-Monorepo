import pytest
from src.reflex import policy, ledger
from src.reflex.core import Reflex
from src.savepoint import logger as splog


def test_policy_enforcement_and_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "LEDGER_DIR", tmp_path / "ledger")
    monkeypatch.setattr(splog, "LOG_DIR", tmp_path / "savepoints")
    r = Reflex()

    policy.set_token("user1")
    check = r.self_check({"bankroll": 1000, "wager": 10, "risk_stats": {"drawdown_p95": 0.25}, "affect": "calm"})
    assert not check["blocked"]
    p1, _ = splog.savepoint_log("e1", {})
    assert p1.parent.name == "user1"
    ledger.record(5.0, outcome=6.0)
    assert (tmp_path / "ledger" / "user1.jsonl").exists()

    policy.set_token("user2")
    check_block = r.self_check({"bankroll": 1000, "wager": 10, "risk_stats": {"drawdown_p95": 0.3}, "affect": "calm"})
    assert check_block["blocked"]
    p2, _ = splog.savepoint_log("e2", {})
    assert p2.parent.name == "user2"

    policy.set_token("legacy")
    check2 = r.self_check({"bankroll": 1000, "wager": 10, "risk_stats": {"drawdown_p95": 0.8}, "affect": "calm"})
    assert not check2["blocked"]
    p3, _ = splog.savepoint_log("e3", {})
    assert p3.parent.name == "legacy"
    policy.set_tool("submit_sim")
    # Dry-run tools bypass risk violations even for explicit policies
    policy.set_token("user2")
    r.self_check({"bankroll": 1000, "wager": 10, "risk_stats": {"drawdown_p95": 0.3}, "affect": "calm"})
