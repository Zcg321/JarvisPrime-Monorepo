import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.tools import roi_attrib


def test_roi_attrib_deterministic(tmp_path):
    own = tmp_path / "own.csv"
    own.write_text("player,own\n")
    roi_attrib.LOG_PATH = tmp_path / "ra.jsonl"
    lineup = {"players": [{"player_id": "p1"}, {"player_id": "p2"}, {"player_id": "p3"}]}
    res1 = roi_attrib.roi_attrib(lineup, str(own), iters=100, seed=42, stack_pairs=True)
    res2 = roi_attrib.roi_attrib(lineup, str(own), iters=100, seed=42, stack_pairs=True)
    assert res1 == res2
    assert len(res1["players"]) == 3
    assert "pairs" in res1 and res1["pairs"]
    assert roi_attrib.LOG_PATH.exists()
    lines = roi_attrib.LOG_PATH.read_text().strip().splitlines()
    assert lines
