import json
import subprocess, sys
from pathlib import Path


def test_dashboard_drilldown(tmp_path, monkeypatch):
    root = Path(tmp_path)
    monkeypatch.chdir(root)
    (root / 'logs/alerts').mkdir(parents=True)
    (root / 'logs/audit').mkdir(parents=True)
    (root / 'logs/savepoints').mkdir(parents=True)
    (root / 'logs/alerts/alerts.jsonl').write_text(json.dumps({'ts': 0, 'type': 'policy', 'severity': 'WARN'}) + '\n')
    (root / 'logs/audit/a.jsonl').write_text(json.dumps({'a': 1}) + '\n')
    (root / 'logs/savepoints/sp.json').write_text(json.dumps({'ts_iso': '2000-01-01T00:00:00Z'}))
    script = Path(__file__).resolve().parents[1] / 'scripts/dashboard.py'
    subprocess.check_call([sys.executable, str(script)], cwd=root)
    data = json.loads((root / 'artifacts/reports/dashboard.json').read_text())
    assert set(data['drilldown'].keys()) == {'alerts', 'audit', 'savepoints'}
    assert all(isinstance(data['drilldown'][k], list) for k in data['drilldown'])
    html = (root / 'artifacts/reports/dashboard.html').read_text()
    assert '<details>' in html
