from src.tools import dfs_engine
from src.tools.dfs_data_sources import mock_source


def test_showdown_lineup():
    players = mock_source.fetch_players()
    res = dfs_engine.showdown_lineup(players, 50000, seed=1)
    lineup = res["lineup"]
    assert len(lineup) == 6
    assert len([p for p in lineup if p.get("slot") == "CPT"]) == 1
    assert res["cost"] <= 50000
    assert len({p["name"] for p in lineup}) == 6
