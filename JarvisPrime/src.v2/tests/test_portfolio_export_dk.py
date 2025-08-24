from pathlib import Path
import importlib

pe = importlib.import_module("src.tools.portfolio_export").portfolio_export

def test_portfolio_export_creates_csv(tmp_path, monkeypatch):
    # use temp dir for artifacts
    monkeypatch.chdir(tmp_path)
    lineups = [{"PG": "p1", "SG": "p2", "SF": "p3", "PF": "p4", "C": "p5", "G": "p2", "F": "p3", "UTIL": "p6"}]
    res = pe("DK_TEST", lineups, "dk_csv", 0)
    csv_path = Path(res["path"])
    assert csv_path.exists()
    manifest = Path("artifacts/exports/dk/MANIFEST.json")
    assert manifest.exists()
