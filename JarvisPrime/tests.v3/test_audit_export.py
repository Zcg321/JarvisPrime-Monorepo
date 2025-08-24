import os
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_audit_export(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    audit = logs / "audit.jsonl"
    lines = [
        json.dumps({"ts": "2025-08-05T00:00:00", "event": "login", "email_masked": "a***@b.com", "ip_hash": "1234567890"}),
        json.dumps({"ts": "2025-09-01T00:00:00", "event": "other", "ip_hash": "zzzzzzzzzz"}),
    ]
    audit.write_text("\n".join(lines))
    env = os.environ.copy()
    cmd = [sys.executable, str(ROOT / "scripts" / "audit_export.py"), "--from", "2025-08-01", "--to", "2025-08-31", "--format", "json", "--rotate"]
    res = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True, env=env)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert len(data) == 1
    assert data[0]["email_masked"].startswith("a***")
    archive = logs / "audit.archive.jsonl"
    assert archive.exists()
    remaining = audit.read_text().strip().splitlines()
    assert len(remaining) == 1
