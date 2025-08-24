import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from jarvis_plugins.app import build_app

def test_autoresurrect_crash():
    c = TestClient(build_app())
    r = c.get("/plugins/debug/crash")
    assert r.status_code == 500
    j = r.json()
    assert j["ok"] is False
    assert j["error"] == "internal_error"
