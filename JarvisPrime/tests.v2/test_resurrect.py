from pathlib import Path
import json

from src.serve import server_stub
from src.core import anchors


def test_resurrect_updates_anchors(tmp_path, monkeypatch):
    tmp_master = tmp_path / "master.json"
    tmp_master.write_text(json.dumps({"foo": "bar"}))
    monkeypatch.setattr(anchors, "MASTER_FILE", tmp_master)
    res = server_stub.router({"tool": "resurrect", "args": {}})
    assert res["ok"]
    assert server_stub.ANCHORS["master"]["foo"] == "bar"
