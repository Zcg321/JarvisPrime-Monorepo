from src.tools import lineup_cover


def test_lineup_cover_minimal_set():
    lineups = [
        {"id": "L1", "players": [{"player_id": "p1", "team": "A"}], "leverage": 0.2, "roi": 0.1},
        {"id": "L2", "players": [{"player_id": "p2", "team": "B"}], "leverage": 0.1, "roi": 0.1},
    ]
    targets = {"players": {"p1": 0.5, "p2": 0.5}, "teams": {}}
    out = lineup_cover.minimize(lineups, targets, seed=1)
    assert out["selected_ids"] == ["L1", "L2"]
    assert out["coverage"]["players"]["p1"] == 0.5
    assert out["coverage"]["players"]["p2"] == 0.5
