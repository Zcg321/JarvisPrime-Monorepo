import json
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.tools import dfs


def test_roi_bias(monkeypatch, tmp_path):
    log = tmp_path / "roi.jsonl"
    lines = [
        {"player": "A", "roi": 0.5},
        {"player": "B", "roi": -0.5},
    ]
    log.write_text("\n".join(json.dumps(x) for x in lines))
    monkeypatch.setattr(dfs, "ROI_LOG", log)
    players = [
        {"name": "A", "pos": "QB", "cost": 10, "proj": 10},
        {"name": "B", "pos": "QB", "cost": 10, "proj": 10},
    ]
    res = dfs.predict_lineup(players, budget=20, roster={"QB": 1}, roi_bias={"lookback_days": 30, "alpha": 0.5})
    assert res["lineup"][0]["name"] == "A"
    assert res["expected"] == 10 * 1.25
    # negative ROI capped at -0.15
    res2 = dfs.predict_lineup([players[1]], budget=20, roster={"QB": 1}, roi_bias={"lookback_days": 30})
    assert res2["expected"] == 10 * 0.85
