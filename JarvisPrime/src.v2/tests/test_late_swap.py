import importlib

ls = importlib.import_module("src.tools.late_swap").late_swap


def test_swaps_out_player(monkeypatch):
    lineup = {"players": [
        {"player_id": "p1", "position": "PG", "salary": 5000, "team": "A", "roi": 0.1, "leverage": 0.1},
        {"player_id": "p2", "position": "SG", "salary": 6000, "team": "B", "roi": 0.1, "leverage": 0.1},
    ]}
    pool = [
        {"player_id": "p3", "position": "PG", "salary": 4800, "team": "C", "roi": 0.2, "leverage": 0.2},
        {"player_id": "p4", "position": "PG", "salary": 7000, "team": "D", "roi": 0.3, "leverage": 0.3},
    ]
    news = [{"player_id": "p1", "status": "out", "ts": "2025-10-25T19:00:00Z"}]
    remaining = [{"team": "C", "start_iso": "2025-10-25T23:30:00Z", "players": pool}]
    res = ls(lineup, news, remaining, {"salary_cap": 50000, "max_from_team": 3}, seed=1)
    ids = [p["player_id"] for p in res["swapped_lineup"]["players"]]
    assert "p1" not in ids and "p4" in ids
    assert res["changes"] == [{"out": "p1", "in": "p4"}]
