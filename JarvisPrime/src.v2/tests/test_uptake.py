import json, pathlib
from src.train import uptake

def test_record(tmp_path):
    uptake.LOG_DIR = tmp_path
    path = uptake.record({"x": 1})
    p = pathlib.Path(path)
    assert p.is_file()
    data = json.loads(p.read_text())
    assert data["x"] == 1
    assert isinstance(data.get("ts"), int)


def test_list_last(tmp_path):
    uptake.LOG_DIR = tmp_path
    first = uptake.record({"a": 1})
    second = uptake.record({"b": 2})
    items = uptake.list_last(2)
    assert len(items) == 2
    # ensure chronological order with latest last
    assert items[-1]["b"] == 2


def test_search(tmp_path):
    uptake.LOG_DIR = tmp_path
    uptake.record({"user": "alpha"})
    uptake.record({"user": "beta"})
    res = uptake.search("alpha", n=5)
    assert len(res) == 1
    assert res[0]["user"] == "alpha"
