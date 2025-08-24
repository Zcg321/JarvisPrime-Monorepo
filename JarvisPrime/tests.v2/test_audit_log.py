import json, hashlib, sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.serve import audit


def test_audit_record_rotation(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "LOG_DIR", tmp_path / "audit")
    monkeypatch.setattr(audit, "LOG_FILE", tmp_path / "audit" / "audit.jsonl")
    audit._line_count = 0
    monkeypatch.setattr(audit, "MAX_LINES", 1)
    audit.record("tool", {"token": "x", "value": 1}, "ABC", "u1", 200)
    lines = audit.LOG_FILE.read_text().strip().splitlines()
    rec = json.loads(lines[0])
    assert rec["args_redacted"]["token"] == "[REDACTED]"
    assert rec["auth_token_hash"] == hashlib.sha256(b"ABC").hexdigest()
    audit.record("tool", {"token": "y"}, "ABC", "u1", 200)
    assert audit.LOG_FILE.exists()
    part = audit.LOG_FILE.with_suffix(".part1")
    assert part.exists()
    lines2 = audit.LOG_FILE.read_text().strip().splitlines()
    assert len(lines2) == 1
