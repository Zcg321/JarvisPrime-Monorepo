import json
from pathlib import Path
from src.tools import dfs_engine
from src.tools.dfs_data_sources import mock_source


def test_ghost_injection(tmp_path, monkeypatch):
    ghost_file = tmp_path / "dfs_ghosts.jsonl"
    ghost_file.write_text(json.dumps({"lineup": [{"name": "A", "pos": "QB", "cost": 5000, "proj": 20}], "ev": 1}) + "\n")
    monkeypatch.setattr(dfs_engine, "GHOST_FILE", ghost_file)
    players = mock_source.fetch_players()
    pool = dfs_engine.lineup_pool(players, 50000, n=1, seed=0)
    assert len(pool) == 2
