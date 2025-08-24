import json, sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from scripts import savepoint_timeline as timeline
from src.savepoint import logger


def test_lineage_chain(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, "LOG_DIR", tmp_path)
    monkeypatch.setattr(timeline, "SAVEPOINT_DIR", tmp_path)
    report = tmp_path / "report.json"
    monkeypatch.setattr(timeline, "REPORT_PATH", report)
    p1, lid1 = logger.savepoint_log("x", {"a": 1})
    import time
    time.sleep(1)
    p2, lid2 = logger.savepoint_log("x", {"a": 2})
    data2 = json.loads(p2.read_text())
    assert data2["parent_id"] == lid1
    timeline.main()
    data = json.loads(report.read_text())
    assert data["events"][1]["parent_id"] == lid1
