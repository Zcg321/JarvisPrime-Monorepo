import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.tools import dfs


def test_multislate_roi_bias(tmp_path, monkeypatch):
    roi_log = tmp_path / "roi.jsonl"
    roi_log.write_text(
        """
{\"ts\":\"2030-01-01T00:00:00\",\"player\":\"A\",\"slate_type\":\"classic\",\"roi\":0.1}
{\"ts\":\"2030-01-01T00:00:00\",\"player\":\"B\",\"slate_type\":\"showdown\",\"roi\":0.1}
""".strip()
    )
    monkeypatch.setattr(dfs, "ROI_LOG", roi_log)
    players = [
        {"name": "A", "cost": 1000, "proj": 10, "pos": "PG"},
        {"name": "B", "cost": 1000, "proj": 10, "pos": "PG"},
    ]
    cfg = {"multi_slate": {"enabled": True, "decay_days": 90, "alpha": 1.0}}
    lineup1 = dfs.predict_lineup(players, 10000, {"UTIL": 1}, cfg)
    lineup2 = dfs.predict_lineup(players, 10000, {"UTIL": 1}, cfg)
    assert lineup1 == lineup2
    assert lineup1["lineup"][0]["name"] == "B"
