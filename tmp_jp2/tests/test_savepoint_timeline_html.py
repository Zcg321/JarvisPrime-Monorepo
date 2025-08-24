import json
import subprocess
import os
from pathlib import Path


def test_timeline_html(tmp_path, monkeypatch):
    logs_dir = Path("logs/reports")
    logs_dir.mkdir(parents=True, exist_ok=True)
    data = [{"ts": 1, "event": "e"}]
    (logs_dir / "savepoint_timeline.json").write_text(json.dumps(data))
    env = dict(os.environ)
    env["PYTHONPATH"] = "."
    subprocess.check_call(["python", "scripts/savepoint_timeline_html.py"], env=env)
    html_path = Path("artifacts/reports/savepoints.html")
    assert html_path.exists()
    text = html_path.read_text()
    assert "Savepoints" in text and "e" in text
