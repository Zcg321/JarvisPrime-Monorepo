import time
from pathlib import Path
import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from scripts import retention_gc


def test_retention_gc(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    old_file = log_dir / "old.log"
    old_file.write_text("x")
    old_time = time.time() - 2 * 86400
    import os
    os.utime(old_file, (old_time, old_time))
    cfg = tmp_path / "retention.yaml"
    cfg.write_text(f"paths:\n  - path: {log_dir}\n    days: 1\n")
    gc_log = tmp_path / "gc.jsonl"
    monkeypatch.setattr(retention_gc, "CFG_PATH", cfg)
    monkeypatch.setattr(retention_gc, "GC_LOG", gc_log)
    retention_gc.gc(dry_run=False)
    assert not old_file.exists()
    assert gc_log.exists()
