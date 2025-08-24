import json
from pathlib import Path
import subprocess
import sys
import json
import tarfile


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj) + "\n")


def test_purge_and_export(tmp_path, monkeypatch):
    root = Path(tmp_path)
    script = Path(__file__).resolve().parents[1] / "scripts/compliance.py"
    monkeypatch.chdir(root)
    (root / "logs/audit").mkdir(parents=True)
    audit = root / "logs/audit/audit.jsonl"
    rec = {"ts_iso": "2025-10-25T12:00:00Z", "tool": "dfs", "token_id": "user1", "result_status": 200}
    audit.write_text(json.dumps(rec) + "\n")
    sp_dir = root / "logs/savepoints"
    sp_dir.mkdir(parents=True)
    sp = sp_dir / "sp.json"
    sp.write_text(json.dumps({"ts_iso": "2025-10-25T12:00:00Z", "token_id": "user1", "event": "e"}))
    cmd = [sys.executable, str(script),
           "export", "--token-id", "user1", "--since", "2025-10-25T00:00Z", "--until", "2025-10-25T23:59Z"]
    out = subprocess.check_output(cmd, cwd=root)
    tar_path = Path(out.decode().strip())
    assert tar_path.exists()
    with tarfile.open(tar_path, "r:gz") as tf:
        names = tf.getnames()
    assert "audit.json" in names and "savepoints.json" in names
    cmd = [sys.executable, str(script),
           "purge", "--token-id", "user1", "--since", "2025-10-25T00:00Z", "--until", "2025-10-25T23:59Z"]
    subprocess.check_call(cmd, cwd=root)
    lines = [json.loads(l) for l in audit.read_text().splitlines()]
    assert lines[0]["tombstone"]
    data = json.loads(sp.read_text())
    assert data["tombstone"]
