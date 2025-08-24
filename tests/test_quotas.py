import json
from datetime import datetime, timezone
from pathlib import Path
import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.serve import quotas


def test_quota_enforcement(tmp_path, monkeypatch):
    path = tmp_path / "usage.jsonl"
    monkeypatch.setattr(quotas, "USAGE_PATH", path)
    cfg = {"default": {"requests": 2}, "overrides": {"tok1": {"requests": 1}}}
    assert quotas.allow("tok1", cfg)
    assert not quotas.allow("tok1", cfg)
    quotas.reset("tok1")
    assert quotas.allow("tok1", cfg)
    quotas.add_cpu("tok1", 50)
    assert quotas.allow("tok2", cfg)
    assert quotas.allow("tok2", cfg)
    assert not quotas.allow("tok2", cfg)
    u = quotas.usage()
    assert u["tok1"]["requests"] == 1
    assert u["tok1"]["cpu_ms"] >= 50
    assert u["tok2"]["requests"] == 2
