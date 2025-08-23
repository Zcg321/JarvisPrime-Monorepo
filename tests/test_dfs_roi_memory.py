from src.tools import dfs_roi_memory, dfs_engine


def test_roi_memory_bias(tmp_path, monkeypatch):
    log = tmp_path / "roi.jsonl"
    monkeypatch.setattr(dfs_roi_memory, "LOG_PATH", log)
    monkeypatch.setattr(dfs_engine.roi_memory, "LOG_PATH", log)
    dfs_roi_memory.record_result(["A"], 10, 30)
    dfs_roi_memory.record_result(["B"], 10, 10)
    z = dfs_roi_memory.rolling_zscores()
    assert "A" in z
    players = [
        {"name": "A", "pos": "QB", "cost": 5000, "proj": 10},
        {"name": "B", "pos": "QB", "cost": 5000, "proj": 10},
    ]
    res = dfs_engine.lineup(players, 5000, {"QB": 1})
    names = [p["name"] for p in res["lineup"]]
    assert names == ["A"]
