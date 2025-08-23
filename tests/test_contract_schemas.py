from fastapi.testclient import TestClient
from jarvis_plugins.app import build_app


def test_contract_toolreply_valid():
    c = TestClient(build_app())
    body = {"text": "{\"tool\":\"search\",\"args\":{\"q\":\"hello\"}}", "schema":"ToolReply"}
    r = c.post("/plugins/tools/validate_contract", json=body)
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["schema"] == "ToolReply"


def test_contract_toolreply_invalid():
    c = TestClient(build_app())
    body = {"text": "{\"args\":{}}", "schema":"ToolReply"}
    r = c.post("/plugins/tools/validate_contract", json=body)
    assert r.status_code == 422
