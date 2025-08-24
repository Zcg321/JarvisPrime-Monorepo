from src.tools import dfs_portfolio


def fake_seed_pool(slate_id, seed, pool_size=50):
    return [
        {"players": [{"player": "PLAYER_1", "team": "A"}]},
        {"players": [{"player": "PLAYER_2", "team": "B"}]},
    ]


def test_portfolio_returns_plan(monkeypatch, tmp_path):
    monkeypatch.setattr(dfs_portfolio.ghost_dfs, "seed_pool", fake_seed_pool)
    res = dfs_portfolio.build(
        slates=[{"id": "S1", "type": "classic"}],
        n_lineups=2,
        as_plan=True,
        bankroll=100.0,
        unit_fraction=0.1,
        entry_fee=10.0,
        max_entries=5,
        seed=1,
    )
    assert "plan" in res and res["plan"]["proposed_entries"] <= 5
    res2 = dfs_portfolio.build(
        slates=[{"id": "S1", "type": "classic"}],
        n_lineups=2,
        as_plan=True,
        bankroll=100.0,
        unit_fraction=0.1,
        entry_fee=10.0,
        max_entries=5,
        seed=1,
    )
    assert res == res2
