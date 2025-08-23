from src.tools import dfs_engine, dfs_exposure
from src.tools.dfs_data_sources import mock_source


def test_pool_and_exposure():
    players = mock_source.fetch_players() + [{"name": "QB2", "pos": "QB", "cost": 4800, "proj": 18}]
    pool = dfs_engine.lineup_pool(players, 50000, n=5, seed=42)
    assert len(pool) >= 5
    names_pool = [[p["name"] for p in lu] for lu in pool]
    selected = dfs_exposure.solve(names_pool, {"A": {"max": 0.6}})
    if selected:
        count = sum("A" in l for l in selected)
        assert count / len(selected) <= 0.6
