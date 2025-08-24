import importlib

submit_plan = importlib.import_module("src.tools.submit_plan").submit_plan

def test_submit_plan_deterministic():
    args = dict(
        date="2025-10-25",
        site="DK",
        modes=["classic"],
        n_lineups=2,
        max_from_team=3,
        seed=1,
        as_plan=True,
        bankroll=1000.0,
        unit_fraction=0.02,
        entry_fee=5.0,
        max_entries=10,
    )
    res1 = submit_plan(**args)
    res2 = submit_plan(**args)
    assert res1 == res2
    assert res1["plan"]["entries"][0]["count"] == 2
    assert res1["status"] in ("ok", "blocked")


def test_submit_plan_blocked(monkeypatch):
    def fake_sim(**kwargs):
        return {"violations": ["bad"]}

    monkeypatch.setattr("src.tools.submit_plan.submit_sim", fake_sim)
    res = submit_plan(
        date="2025-10-25",
        site="DK",
        modes=["classic"],
        n_lineups=1,
        max_from_team=3,
        seed=1,
        as_plan=True,
        bankroll=1000.0,
        unit_fraction=0.02,
        entry_fee=5.0,
        max_entries=10,
    )
    assert res["status"] == "blocked"
