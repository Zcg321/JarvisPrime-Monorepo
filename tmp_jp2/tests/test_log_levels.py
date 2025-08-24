import json
import urllib.request
import importlib
from pathlib import Path


def test_log_level_filter(tmp_path, monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    from src.serve import logging as slog
    importlib.reload(slog)
    monkeypatch.setattr(slog, "LOG_PATH", tmp_path / "server.log")
    slog.log("info", "ignore")
    slog.log("error", "keep")
    lines = slog.LOG_PATH.read_text().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["msg"] == "keep"
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    importlib.reload(slog)


def test_compact_error(server):
    port = server
    req = urllib.request.Request(f"http://127.0.0.1:{port}/badpath")
    try:
        urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        data = json.loads(e.read())
        assert data["error"] == "not_found"
        assert "detail" not in data
    else:
        assert False
