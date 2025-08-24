import sys, pathlib, json, importlib
from pathlib import Path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))


def test_roi_explain(tmp_path, monkeypatch):
    reports = tmp_path / "reports"
    reports.mkdir(parents=True)
    attrib = reports / "roi_attrib.jsonl"
    attrib.write_text(json.dumps({"result": {"players": [{"player_id": "p1", "mc": 1.0}]}}) + "\n")
    ghost_dir = tmp_path / "ghosts"
    ghost_dir.mkdir(parents=True)
    (ghost_dir / "roi_daily.jsonl").write_text(json.dumps({"ts": 0, "slate_type": "classic", "roi": 0.1}) + "\n")
    monkeypatch.setenv("ROI_LOG_DIR_LEGACY", str(ghost_dir))
    monkeypatch.setenv("ROI_ATTRIB_LOG", str(attrib))
    import src.tools.roi_cohorts as roi_cohorts
    import scripts.roi_explain as roi_explain
    importlib.reload(roi_cohorts)
    importlib.reload(roi_explain)
    data = roi_explain.build()
    assert data["players"][0]["player_id"] == "p1"
    html = Path("artifacts/reports/roi_explain.html").read_text()
    assert "Players" in html
