from pathlib import Path
import json
import subprocess
import sys

def test_dashboard_outputs(tmp_path, monkeypatch):
    root = Path(tmp_path)
    script = Path(__file__).resolve().parents[1] / "scripts/dashboard.py"
    monkeypatch.chdir(root)
    (root / "logs/audit").mkdir(parents=True)
    (root / "logs/savepoints").mkdir(parents=True)
    subprocess.check_call([sys.executable, str(script)], cwd=root)
    j = root / "artifacts/reports/dashboard.json"
    h = root / "artifacts/reports/dashboard.html"
    assert j.exists() and h.exists()
    data = json.loads(j.read_text())
    assert "metrics" in data and "alerts" in data
    assert "<h2>Health" in h.read_text()
