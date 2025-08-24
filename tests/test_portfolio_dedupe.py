import importlib

pd = importlib.import_module("src.tools.portfolio_dedupe").portfolio_dedupe


def test_dedupe_drops_near_duplicates():
    lineups = [
        {"id": "A", "players": [{"player_id": "p1"}, {"player_id": "p2"}, {"player_id": "p3"}], "roi": 0.1},
        {"id": "B", "players": [{"player_id": "p1"}, {"player_id": "p2"}, {"player_id": "p3"}], "roi": 0.2},
        {"id": "C", "players": [{"player_id": "p1"}, {"player_id": "p4"}, {"player_id": "p3"}], "roi": 0.3},
        {"id": "D", "players": [{"player_id": "p5"}, {"player_id": "p6"}, {"player_id": "p7"}], "roi": 0.4},
    ]
    res = pd(lineups, max_dupe=1, min_hamming=2, seed=1)
    assert res["kept_ids"] == ["D", "C"]
    assert set(res["dropped_ids"]) == {"A", "B"}
    assert res["stats"]["dup_removed"] == 2
