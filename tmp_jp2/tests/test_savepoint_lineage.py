from pathlib import Path
import json

from src.savepoint import logger
from src.reflex import policy


def test_lineage_chain(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, "LOG_DIR", tmp_path / "sp")
    import src.savepoint.lineage as lineage
    monkeypatch.setattr(lineage, "BASE", tmp_path / "sp")
    policy.set_token("t1")
    f1, id1 = logger.savepoint_log("e", {})
    f2, id2 = logger.savepoint_log("e", {})
    assert json.loads(f2.read_text())["parent_id"] == id1
    ptr = tmp_path / "sp" / "t1" / "__last" / "e.json"
    assert ptr.exists()
