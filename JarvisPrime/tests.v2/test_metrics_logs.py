from fastapi.testclient import TestClient
from pathlib import Path
import json


def test_metrics_endpoint_and_logging(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_LOG_DIR", str(tmp_path))
    import importlib
    import jarvis_plugins.logger as logger
    importlib.reload(logger)
    import jarvis_plugins.savepoint as sp_mod
    importlib.reload(sp_mod)
    from jarvis_plugins.savepoint import SavepointLogger
    sp = SavepointLogger(base_dir=str(tmp_path / "sps"))
    sp.create({"foo": "bar"}, tag="t1")
    logf = Path(tmp_path) / "jarvis.log"
    assert logf.exists()
    lines = logf.read_text().splitlines()
    j = json.loads(lines[-1])
    assert j["event"] == "savepoint"
    from jarvis_plugins.app import build_app
    c = TestClient(build_app())
    r = c.get("/plugins/metrics")
    assert r.status_code == 200
    assert "uptime_sec" in r.json()
