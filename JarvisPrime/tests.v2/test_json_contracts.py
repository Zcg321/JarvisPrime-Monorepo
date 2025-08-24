from fastapi.testclient import TestClient
from jarvis_plugins.app import build_app

def test_json_guard_positive():
    c = TestClient(build_app())
    r = c.post("/plugins/tools/validate_json", json={"text": "{\"ok\": true}"})
    assert r.status_code == 200
    assert r.json()["ok"] is True

def test_json_guard_negative():
    c = TestClient(build_app())
    r = c.post("/plugins/tools/validate_json", json={"text": "bad"})
    assert r.status_code == 422
