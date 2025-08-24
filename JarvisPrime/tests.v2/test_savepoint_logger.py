import json
import hashlib
import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.savepoint import logger

def test_savepoint_basic(monkeypatch, tmp_path):
    monkeypatch.setattr(logger, "LOG_DIR", tmp_path)
    p1, lid1 = logger.savepoint_log("first", {"token": "abc", "x": 1}, "calm", 50.0)
    p2, lid2 = logger.savepoint_log("second", {"api": "key", "nested": {"secret": "s"}}, None, None)
    assert p1.exists() and p2.exists() and lid1 and lid2
    data = json.loads(p1.read_text())
    assert data["payload"]["token"] == "[REDACTED]"
    payload_json = json.dumps({"token": "[REDACTED]", "x": 1}, sort_keys=True, separators=(",", ":"))
    assert data["sha256_payload"] == hashlib.sha256(payload_json.encode()).hexdigest()
    assert not any(tmp_path.glob("*.tmp"))
