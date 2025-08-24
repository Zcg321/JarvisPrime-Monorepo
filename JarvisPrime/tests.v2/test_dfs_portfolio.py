from src.tools import dfs_portfolio


def fake_seed_pool(slate_id, seed, pool_size=50):
    return [
        {"players": [{"player": "PLAYER_123", "team": "A"}]},
        {"players": [{"player": "P2", "team": "B"}]},
    ]


def test_portfolio_respects_caps(monkeypatch):
    monkeypatch.setattr(dfs_portfolio.ghost_dfs, "seed_pool", fake_seed_pool)
    res = dfs_portfolio.build(
        slates=[{"id": "S1", "type": "classic"}, {"id": "S2", "type": "classic"}],
        n_lineups=2,
        global_exposure_caps={"PLAYER_123": 0.5},
        seed=1,
    )
    count = sum(
        1 for l in res["lineups"] if any(p.get("player") == "PLAYER_123" for p in l["players"])
    )
    assert count <= 1
    assert res["exposure_report"]["PLAYER_123"] == {"count": 1, "exposure": 0.5}
    assert sum(a["lineups"] for a in res["slate_allocations"]) == len(res["lineups"])
    assert res["leftover_stats"] == {"mean": 0, "p95": 0, "max": 0}
    res2 = dfs_portfolio.build(
        slates=[{"id": "S1", "type": "classic"}, {"id": "S2", "type": "classic"}],
        n_lineups=2,
        global_exposure_caps={"PLAYER_123": 0.5},
        seed=1,
    )
    assert res == res2
