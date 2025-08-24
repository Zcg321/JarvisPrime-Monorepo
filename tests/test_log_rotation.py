from pathlib import Path
import os, sys
sys.path.insert(0, os.getcwd())
from src.serve import logging as slog


def test_log_rotation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    slog.LOG_PATH = Path("logs/server.log")
    slog.MAX_BYTES = 100
    slog.MAX_FILES = 3
    for i in range(40):
        slog.log("info", "x" * 50)
    files = sorted(Path("logs").glob("server.log*"))
    assert len(files) <= 3
