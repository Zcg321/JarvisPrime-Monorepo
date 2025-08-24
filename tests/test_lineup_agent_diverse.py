import importlib

lineup_agent_module = importlib.import_module("src.tools.lineup_agent")
lineup_agent_diverse = lineup_agent_module.lineup_agent_diverse
lineup_agent = lineup_agent_module.lineup_agent

def test_lineup_agent_diverse_deterministic():
    seed_lineup = {"id": "L1", "players": [{"player_id": "p1"}]}
    r1 = lineup_agent_diverse(seed_lineup=seed_lineup, seed=1)
    r2 = lineup_agent_diverse(seed_lineup=seed_lineup, seed=1)
    assert r1 == r2
    assert r1["diversity_metric"] >= 0
    # baseline agent returns same lineup without diversity metric
    base = lineup_agent(seed_lineup=seed_lineup, seed=1)
    assert base["best_lineup"] == r1["best_lineup"]
