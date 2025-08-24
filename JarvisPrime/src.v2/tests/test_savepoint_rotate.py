import os
import time
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.savepoint import logger


def test_savepoint_rotate(monkeypatch, tmp_path):
    monkeypatch.setattr(logger, "LOG_DIR", tmp_path)
    now = time.time()
    for i in range(550):
        f = tmp_path / f"{i}.json"
        f.write_text("{}")
        mtime = now - 20 * 86400 if i < 100 else now
        os.utime(f, (mtime, mtime))
    removed = logger.rotate_logs(keep=500, days=14)
    remaining = list(tmp_path.glob("*.json"))
    assert len(remaining) <= 500
    cutoff = now - 14 * 86400
    assert all(f.stat().st_mtime >= cutoff for f in remaining)
    assert removed >= 100
