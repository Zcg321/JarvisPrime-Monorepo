from src.tools.roi_report import generate
import json, os, pathlib


def test_roi_report_ranks(tmp_path):
    log = tmp_path / "roi.jsonl"
    lines = [
        {"player_id":"A","roi":0.1},
        {"player_id":"B","roi":0.5},
        {"player_id":"A","roi":0.2},
        {"player_id":"C","roi":-0.3},
    ]
    with open(log, "w", encoding="utf-8") as fh:
        for l in lines:
            fh.write(json.dumps(l)+"\n")
    rep = generate(30, str(log))
    assert rep["top"][0]["player_id"] == "B"
    assert rep["bottom"][-1]["player_id"] == "C"
