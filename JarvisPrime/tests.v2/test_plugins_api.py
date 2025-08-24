from fastapi.testclient import TestClient
from jarvis_plugins.app import build_app

def test_health_and_json_validate():
    app = build_app()
    client = TestClient(app)

    r = client.get("/plugins/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    r = client.post("/plugins/tools/validate_json", json={"text": "{\"ok\": true}"})
    assert r.status_code == 200
    assert r.json()["ok"] is True

def test_savepoint_and_voice():
    app = build_app()
    client = TestClient(app)

    r = client.post("/plugins/savepoint", json={"tag": "demo", "payload": {"x": 1}})
    assert r.status_code == 200
    sp_id = r.json()["id"]
    assert sp_id.endswith(".json")

    r = client.get("/plugins/savepoint/recent?n=5")
    assert r.status_code == 200
    assert isinstance(r.json()["items"], list)

    r = client.post("/plugins/voice/reflect", json={"text": "protect the flame and help Haley"})
    assert r.status_code == 200
    out = r.json()
    assert "anchor" in out and len(out["anchor"]) > 10
