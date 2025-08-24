import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.tools import submit_sim


def test_submit_sim_guard():
    plan = {"entries": [{"slate_id": "s", "type": "classic", "count": 1, "entry_fee": 10.0}]}
    res = submit_sim.submit_sim(100.0, plan, iters=100, seed=1, guards={"max_drawdown_p95": 0.01})
    assert "max_drawdown_p95" in res["violations"]
    res2 = submit_sim.submit_sim(100.0, plan, iters=100, seed=1, guards={"max_drawdown_p95": 1.0})
    assert "max_drawdown_p95" not in res2["violations"]
    assert res2["p50"] == res["p50"]
