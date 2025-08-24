from src.tools import lineup_agent


def test_lineup_agent_deterministic():
    seed = {"players": [{"player_id": "p1"}]}
    res = lineup_agent.lineup_agent(seed, beam=2, depth=2, seed=1337)
    assert res["best_lineup"] == seed
    assert res["beam_trail"] == [seed]
