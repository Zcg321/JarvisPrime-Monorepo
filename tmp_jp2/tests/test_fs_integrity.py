from scripts.fs_integrity_check import run
from pathlib import Path
import json


def test_fs_integrity(tmp_path, monkeypatch):
    # create structure
    d = tmp_path / "logs/savepoints"
    d.mkdir(parents=True)
    jf = d / "a.json"
    jf.write_text("{}")
    tmp = d / "b.tmp"
    tmp.write_text("x")
    monkeypatch.chdir(tmp_path)
    res = run()
    assert res["tmp_cleaned"] == 1
