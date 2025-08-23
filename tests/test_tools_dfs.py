from src.tools import dfs_engine
from src.tools.dfs_data_sources import mock_source

def test_dfs_lineup_under_budget():
    players = mock_source.fetch_players()
    result = dfs_engine.lineup(players, 50000)
    assert result["lineup"]
    assert result["cost"] <= 50000

def test_dfs_roi_calc():
    roi = dfs_engine.roi([{"profit": 50, "cost": 100}])
    assert abs(roi + 0.5) < 1e-6
