import json
from pathlib import Path
import subprocess, sys


def test_dashboard_trends(tmp_path, monkeypatch):
    root = Path(tmp_path)
    monkeypatch.chdir(root)
    (root / 'logs/alerts').mkdir(parents=True)
    (root / 'logs/savepoints').mkdir(parents=True)
    (root / 'logs/audit').mkdir(parents=True)
    script = Path(__file__).resolve().parents[1] / 'scripts/dashboard.py'
    subprocess.check_call([sys.executable, str(script)], cwd=root)
    data = json.loads((root / 'artifacts/reports/dashboard.json').read_text())
    assert set(data['trends'].keys()) == {'alerts', 'audit', 'savepoints'}
    assert all(len(v) == 7 for v in data['trends'].values())
    html = (root / 'artifacts/reports/dashboard.html').read_text()
    assert '<svg' in html
