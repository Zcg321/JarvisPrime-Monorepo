import math
from src.reflex.core import Reflex

def test_affect_bias_confident_anxious():
    r = Reflex()
    r.choose_action([{"weight": 1.0, "source_weight": 1.0}], affect="anxious")
    score_anxious = r.history[-1]["scores"][0][0]
    assert math.isclose(score_anxious, 0.9, rel_tol=1e-6)

    r.choose_action([{"weight": 1.0, "source_weight": 1.0}], affect="confident")
    score_confident = r.history[-1]["scores"][0][0]
    assert math.isclose(score_confident, 1.2, rel_tol=1e-6)


def test_self_check_flags():
    r = Reflex()
    ok = r.self_check({"bankroll": 10, "needs_tool": True, "uses_local": False, "uses_rag": True, "risk": 0.5, "risk_limit": 1})
    assert ok["bankroll_ok"] and ok["tool_needed"]
    assert ok["uses_local_or_rag"] and ok["within_risk"]

    bad = r.self_check({"bankroll": -1, "needs_tool": False, "uses_local": False, "uses_rag": False, "risk": 2, "risk_limit": 1})
    assert not bad["bankroll_ok"]
    assert not bad["uses_local_or_rag"]
    assert not bad["within_risk"]


def test_feedback_adjusts_source_bias(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    r = Reflex()
    # baseline score
    r.choose_action([{"weight": 1, "source_weight": 1, "source": "dfs"}])
    base = r.history[-1]["scores"][0][0]
    assert math.isclose(base, 1.0, rel_tol=1e-6)
    # positive feedback boosts bias
    r.feedback("dfs", True)
    r.choose_action([{"weight": 1, "source_weight": 1, "source": "dfs"}])
    boosted = r.history[-1]["scores"][0][0]
    assert boosted > base
    # negative feedback lowers bias
    r.feedback("dfs", False)
    r.choose_action([{"weight": 1, "source_weight": 1, "source": "dfs"}])
    lowered = r.history[-1]["scores"][0][0]
    assert lowered < boosted


def test_bias_persistence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    r = Reflex()
    r.feedback("dfs", True)
    bias = r.source_bias["dfs"]
    r2 = Reflex()
    assert r2.source_bias.get("dfs") == bias
