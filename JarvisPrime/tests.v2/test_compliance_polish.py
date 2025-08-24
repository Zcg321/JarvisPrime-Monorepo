import json
import subprocess
import sys
from pathlib import Path


def test_compliance_simulate(tmp_path, monkeypatch):
    root = Path(tmp_path)
    script = Path(__file__).resolve().parents[1] / "scripts/compliance.py"
    monkeypatch.chdir(root)
    (root / "logs/audit").mkdir(parents=True)
    (root / "logs/audit/a.jsonl").write_text(json.dumps({"ts_iso": "2025-10-25T12:00:00Z", "token_id": "user1", "tool": "t"}) + "\n")
    (root / "logs/savepoints").mkdir(parents=True)
    out = subprocess.check_output([
        sys.executable,
        str(script),
        "purge",
        "--simulate",
        "--confirm",
        "--token-id",
        "user1",
    ], cwd=root)
    assert b"would_purge" in out
